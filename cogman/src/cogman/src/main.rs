//! cogman — unified init, package manager, supervisor, and health monitor.
//!
//! Modes:
//!   cogman daemon              Run as PID 1 / init daemon (supervisor loop).
//!   cogman svc list|status|… Control running daemon over Unix socket.
//!   cogman pkg install|…       Package management.

mod db;
mod installer;
mod policy;
mod supervisor;
mod ctl;

use std::path::{Path, PathBuf};
use std::sync::Arc;
use std::thread;

use clap::{Parser, Subcommand};

use ctl::{send, parse_response, SOCK_PATH};
use installer::Installer;
use supervisor::Supervisor;

// ── CLI ───────────────────────────────────────────────────────────────────

#[derive(Parser)]
#[command(
    name    = "cogman",
    version = "2.0.0",
    about   = "Unified init, supervisor, and package manager for Rogue Linux",
)]
struct Cli {
    /// Unix socket path for daemon control.
    #[arg(long, default_value = SOCK_PATH, env = "COGMAN_SOCK")]
    sock: PathBuf,

    #[command(subcommand)]
    cmd: TopCmd,
}

#[derive(Subcommand)]
enum TopCmd {
    /// Run as init/supervisor daemon (blocking).
    Daemon {
        /// Directory containing *.service files.
        #[arg(long, default_value = "/etc/cogman/services")]
        services: PathBuf,
    },

    /// Control the running daemon.
    #[command(subcommand)]
    Svc(SvcCmd),

    /// Package management.
    #[command(subcommand)]
    Pkg(PkgCmd),
}

#[derive(Subcommand)]
enum SvcCmd {
    /// List all services.
    List,
    /// Show service status.
    Status { name: String },
    /// Start a stopped/failed service.
    Start { name: String },
    /// Stop a running service.
    Stop { name: String },
    /// Restart a service.
    Restart { name: String },
    /// Ping the daemon (liveness check).
    Ping,
}

#[derive(Subcommand)]
enum PkgCmd {
    /// Install a package from a .toml definition.
    Install {
        /// Path to <package>.toml.
        toml: PathBuf,
        /// Installation root (default: /).
        #[arg(long)]
        root: Option<PathBuf>,
        /// Directory containing built packages.
        #[arg(long, default_value = "/var/cache/cogman/packages")]
        packages_dir: PathBuf,
    },
    /// Remove an installed package.
    Remove {
        name: String,
        #[arg(long, default_value = "/var/cache/cogman/packages")]
        packages_dir: PathBuf,
    },
    /// Upgrade (remove + re-install) a package.
    Upgrade {
        toml: PathBuf,
        #[arg(long)]
        root: Option<PathBuf>,
        #[arg(long, default_value = "/var/cache/cogman/packages")]
        packages_dir: PathBuf,
    },
    /// List installed packages.
    List {
        #[arg(long, default_value = "/var/cache/cogman/packages")]
        packages_dir: PathBuf,
    },
}

// ── Entry point ───────────────────────────────────────────────────────────

fn main() {
    let cli = Cli::parse();

    match cli.cmd {
        TopCmd::Daemon { services } => run_daemon(&services, &cli.sock),
        TopCmd::Svc(cmd)            => run_svc(cmd, &cli.sock),
        TopCmd::Pkg(cmd)            => run_pkg(cmd),
    }
}

// ── Daemon ────────────────────────────────────────────────────────────────

fn run_daemon(services_dir: &Path, sock_path: &Path) {
    let pid = std::process::id();
    eprintln!();
    eprintln!("\x1b[1m\x1b[96m  ╔══════════════════════════════════════════════════════╗\x1b[0m");
    eprintln!("\x1b[1m\x1b[96m  ║       ▐ C O G M A N ▌  Process Supervisor            ║\x1b[0m");
    eprintln!("\x1b[96m  ║   Your faithful systems steward is standing by, sir.  ║\x1b[0m");
    eprintln!("\x1b[90m  ║   PID: {:<46} ║\x1b[0m", pid);
    eprintln!("\x1b[1m\x1b[96m  ╚══════════════════════════════════════════════════════╝\x1b[0m");
    eprintln!();

    let sup = Arc::new(Supervisor::new());
    sup.load_dir(services_dir);

    // Control socket thread
    let sup_ctl  = Arc::clone(&sup);
    let sock_buf = sock_path.to_path_buf();
    thread::spawn(move || ctl::serve(&sock_buf, sup_ctl));

    eprintln!("\x1b[92mAll preparations complete, sir. Entering the supervision loop.\x1b[0m");
    eprintln!("\x1b[90m  (I shall not trouble you further unless something requires your attention.)\x1b[0m");
    eprintln!();

    // Supervision loop (blocks forever)
    sup.run();
}

// ── Service control ───────────────────────────────────────────────────────

fn run_svc(cmd: SvcCmd, sock: &Path) {
    let (verb, arg) = match &cmd {
        SvcCmd::List              => ("LIST".to_string(),            String::new()),
        SvcCmd::Status { name }   => ("STATUS".to_string(),          name.clone()),
        SvcCmd::Start  { name }   => ("START".to_string(),           name.clone()),
        SvcCmd::Stop   { name }   => ("STOP".to_string(),            name.clone()),
        SvcCmd::Restart { name }  => ("RESTART".to_string(),         name.clone()),
        SvcCmd::Ping              => ("PING".to_string(),             String::new()),
    };

    let request = if arg.is_empty() { verb } else { format!("{verb} {arg}") };

    match send(sock, &request) {
        Err(e) => {
            eprintln!("\x1b[91mI'm afraid I cannot reach the daemon, sir.\x1b[0m");
            eprintln!("\x1b[91m  Is it running? ({})\x1b[0m", e);
            eprintln!("\x1b[90m  Hint: 'cogman daemon --services /etc/cogman/services' to start it.\x1b[0m");
            std::process::exit(1);
        }
        Ok(raw) => match parse_response(&raw) {
            Ok(payload) => print!("{payload}"),
            Err(e) => {
                eprintln!("\x1b[91mI'm afraid the daemon reports an issue, sir:\x1b[0m");
                eprintln!("\x1b[91m  {e}\x1b[0m");
                std::process::exit(1);
            }
        }
    }
}

// ── Package management ────────────────────────────────────────────────────

fn run_pkg(cmd: PkgCmd) {
    match cmd {
        PkgCmd::Install { toml, root, packages_dir } => {
            let mut inst = open_installer(&packages_dir, root.as_deref());
            // Warn if the package is already installed
            let pkg_name = toml.file_stem()
                .and_then(|s| s.to_str()).unwrap_or("unknown");
            if inst.is_installed(pkg_name) {
                eprintln!(
                    "\x1b[93m\x1b[1mAhem.\x1b[0m \x1b[93mForgive me for saying so, sir, but '{}' is already very much in residence. \
                     One wonders what prompted a second installation. \
                     Perhaps 'cogman pkg upgrade' was the intended order?\x1b[0m",
                    pkg_name
                );
                // Proceed anyway — user may be re-installing intentionally
            }
            match inst.install(&toml) {
                Ok(rec) => println!(
                    "\x1b[1m\x1b[33m  ████  Magnificent, your highness!\x1b[0m \
                     \x1b[92m'{}' v{} has been installed and stands ready for duty.\x1b[0m",
                    rec.name, rec.version
                ),
                Err(e)  => {
                    eprintln!("\x1b[91mI'm afraid the installation has come a cropper, sir:\x1b[0m");
                    eprintln!("\x1b[91m  {e}\x1b[0m");
                    std::process::exit(1);
                }
            }
        }
        PkgCmd::Remove { name, packages_dir } => {
            let mut inst = open_installer(&packages_dir, None);
            match inst.remove(&name) {
                Ok(()) => println!("\x1b[92mVery good, sir. '{}' has been cleanly removed from the premises.\x1b[0m", name),
                Err(e) => {
                    eprintln!("\x1b[91mI'm afraid the removal has encountered a difficulty, sir:\x1b[0m");
                    eprintln!("\x1b[91m  {e}\x1b[0m");
                    std::process::exit(1);
                }
            }
        }
        PkgCmd::Upgrade { toml, root, packages_dir } => {
            let mut inst = open_installer(&packages_dir, root.as_deref());
            match inst.upgrade(&toml) {
                Ok(rec) => println!(
                    "\x1b[1m\x1b[33m  ████  Splendid, your highness!\x1b[0m \
                     \x1b[92m'{}' has been brought fully up to date — v{} is now in service.\x1b[0m",
                    rec.name, rec.version
                ),
                Err(e)  => {
                    eprintln!("\x1b[91mMost regrettably, the upgrade has not gone to plan, sir:\x1b[0m");
                    eprintln!("\x1b[91m  {e}\x1b[0m");
                    std::process::exit(1);
                }
            }
        }
        PkgCmd::List { packages_dir } => {
            let inst = open_installer(&packages_dir, None);
            let pkgs = inst.list_installed();
            if pkgs.is_empty() {
                println!("\x1b[90mThe package ledger is quite empty, sir. Nothing has been installed as yet.\x1b[0m");
                println!("\x1b[90mMight I suggest 'cogman pkg install <package.toml>' to get started?\x1b[0m");
            } else {
                println!("\x1b[1m\x1b[96mThe following {} package(s) are currently installed, sir:\x1b[0m", pkgs.len());
                println!("\x1b[90m  ────────────────────────────────────────────────\x1b[0m");
                for p in &pkgs { println!("  \x1b[97m{p}\x1b[0m"); }
                println!("\x1b[90m  ────────────────────────────────────────────────\x1b[0m");
            }
        }
    }
}

fn open_installer(packages_dir: &Path, root: Option<&Path>) -> Installer {
    match Installer::new(packages_dir, root) {
        Ok(i)  => i,
        Err(e) => {
            eprintln!("\x1b[91mI'm afraid I cannot open the package ledger, my lord:\x1b[0m");
            eprintln!("\x1b[91m  {e}\x1b[0m");
            eprintln!("\x1b[90m  Ensure the packages directory exists and is accessible.\x1b[0m");
            std::process::exit(1);
        }
    }
}
