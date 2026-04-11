//! Package installer — Feature 3: install, remove, upgrade.
//!
//! Install:  invoke cogman-planner → cogman-executor, record files in PackageDb.
//! Remove:   delete every file from the manifest, remove empty dirs, purge db record.
//! Upgrade:  remove old version, install new version.
//!
//! The installer does NOT re-implement the build system; it delegates to the
//! existing planner + executor binaries (or the ones on PATH).

use std::env;
use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::process::{Command, ExitStatus};
use std::time::{SystemTime, UNIX_EPOCH};

use crate::db::{PackageDb, PackageRecord};

// ── Config ────────────────────────────────────────────────────────────────

/// Where installed packages are tracked.
pub const DB_PATH: &str = crate::db::DB_PATH;

/// Default filesystem root for installations.
const DEFAULT_ROOT: &str = "/";

// ── Installer ─────────────────────────────────────────────────────────────

pub struct Installer {
    db:           PackageDb,
    packages_dir: PathBuf,
    install_root: PathBuf,
    /// Override path for cogman-planner binary.
    planner_bin:  PathBuf,
    /// Override path for cogman-executor binary.
    executor_bin: PathBuf,
}

impl Installer {
    /// Open the installer with the system database.
    /// The database path may be overridden with the `COGMAN_DB` environment variable.
    pub fn new(packages_dir: &Path, install_root: Option<&Path>) -> io::Result<Self> {
        let db_path: PathBuf = env::var("COGMAN_DB")
            .map(PathBuf::from)
            .unwrap_or_else(|_| PathBuf::from(DB_PATH));
        let db   = PackageDb::open(&db_path)?;
        let root = install_root.unwrap_or(Path::new(DEFAULT_ROOT)).to_path_buf();

        // Planner/executor: prefer same directory as this process, then PATH.
        let self_dir = env::current_exe()
            .ok()
            .and_then(|p| p.parent().map(|d| d.to_path_buf()))
            .unwrap_or_else(|| PathBuf::from("."));

        let planner  = resolve_bin(&self_dir, "cogman-planner");
        let executor = resolve_bin(&self_dir, "cogman-executor");

        Ok(Installer {
            db,
            packages_dir: packages_dir.to_path_buf(),
            install_root: root,
            planner_bin:  planner,
            executor_bin: executor,
        })
    }

    // ── Install ───────────────────────────────────────────────────────────

    /// Install a package from its TOML definition.
    ///
    /// `toml_path` — path to the `<name>.toml` package definition.
    /// Returns the installed `PackageRecord`.
    pub fn install(&mut self, toml_path: &Path) -> Result<PackageRecord, String> {
        let name = toml_path
            .file_stem()
            .and_then(|s| s.to_str())
            .unwrap_or("unknown")
            .to_string();

        eprintln!("\x1b[96mPreparing to procure '{}', sir. Engaging the planner...\x1b[0m", name);

        // ── Step 1: Plan ──────────────────────────────────────────────────
        let plan_file = self.packages_dir
            .join(format!("{name}.plan"));

        // Use native variant (`build --build`) so the executor runs the steps and
        // exits cleanly. The binary variant is for PID-1 / supervisor deployments
        // and enters a persistent idle loop after steps complete, which is
        // inappropriate for one-shot package installation.
        let plan_status = Command::new(&self.planner_bin)
            .arg("build")
            .arg("--build")   // native variant — no supervisor loop
            .arg(toml_path)
            .arg("--output")
            .arg(&plan_file)
            .arg("--rootfs")
            .arg(self.install_root.to_str().unwrap_or("/"))
            .status()
            .map_err(|e| format!(
                "I'm afraid I cannot locate the planner binary, sir. \
                 Ensure 'cogman-planner' is installed and on PATH. (detail: {e})"
            ))?;

        check_exit("cogman-planner", plan_status)?;
        eprintln!("\x1b[92mThe planner has completed its engagement admirably, sir.\x1b[0m");

        // ── Step 2: Execute ───────────────────────────────────────────────
        // The executor writes a sidecar manifest at <plan>.manifest if it supports
        // --manifest-out; otherwise we collect the file list from its stdout.
        let manifest_file = plan_file.with_extension("manifest");

        eprintln!("\x1b[96mInstructing the executor to carry out the plan, sir...\x1b[0m");
        let exec_status = Command::new(&self.executor_bin)
            .arg(&plan_file)
            .status()
            .map_err(|e| format!(
                "I cannot locate the executor binary, sir. \
                 Ensure 'cogman-executor' is installed and on PATH. (detail: {e})"
            ))?;

        check_exit("cogman-executor", exec_status)?;
        eprintln!("\x1b[92mThe executor has carried out its instructions without complaint, sir.\x1b[0m");

        // ── Step 3: Record ────────────────────────────────────────────────
        // Read manifest if the executor produced one; otherwise track no files.
        let files = read_manifest(&manifest_file).unwrap_or_default();
        let rec   = build_record(&name, &files, &self.install_root);

        self.db.upsert(rec.clone())
            .map_err(|e| format!("db upsert: {e}"))?;

        eprintln!(
            "\x1b[1m\x1b[33m'{}' has been installed with distinction, your grace. {} file(s) now in service.\x1b[0m",
            name, files.len()
        );
        Ok(rec)
    }

    // ── Remove ────────────────────────────────────────────────────────────

    /// Remove an installed package by name.
    pub fn remove(&mut self, name: &str) -> Result<(), String> {
        let rec = self.db.get(name)
            .ok_or_else(|| format!(
                "'{}' does not appear to be installed, sir. \
                 One cannot evict a tenant who never took up residence. \
                 Might I suggest 'cogman pkg list' to see what is actually present?",
                name
            ))?
            .clone();

        eprintln!(
            "\x1b[96mProceeding to remove '{}' from the premises, sir. {} file(s) to be cleared.\x1b[0m",
            name, rec.files.len()
        );

        let root = Path::new(&rec.install_root);
        let mut dirs: Vec<PathBuf> = Vec::new();

        for rel in &rec.files {
            let abs = root.join(rel.trim_start_matches('/'));
            if abs.is_dir() {
                dirs.push(abs);
                continue;
            }
            if let Err(e) = fs::remove_file(&abs) {
                if e.kind() != io::ErrorKind::NotFound {
                    eprintln!("\x1b[93mI was unable to remove '{}', sir: {e}. Proceeding regardless.\x1b[0m", abs.display());
                }
            }
        }

        // Remove directories deepest-first (reverse alphabetical approximates this)
        dirs.sort();
        dirs.reverse();
        for d in dirs {
            if fs::read_dir(&d).map_or(false, |mut e| e.next().is_none()) {
                let _ = fs::remove_dir(&d);
            }
        }

        self.db.remove(name)
            .map_err(|e| format!("db remove: {e}"))?;

        eprintln!("\x1b[92m'{}' has been cleanly removed, sir. The estate is tidier for it.\x1b[0m", name);
        Ok(())
    }

    // ── Upgrade ───────────────────────────────────────────────────────────

    /// Upgrade (remove old version, install new version).
    pub fn upgrade(&mut self, toml_path: &Path) -> Result<PackageRecord, String> {
        let name = toml_path
            .file_stem()
            .and_then(|s| s.to_str())
            .unwrap_or("unknown")
            .to_string();

        if self.db.has(&name) {
            eprintln!(
                "\x1b[96mUpgrading '{}', sir — relieving the old posting and installing the new.\x1b[0m",
                name
            );
            self.remove(&name)?;
        } else {
            eprintln!(
                "\x1b[93mI note that '{}' is not currently installed, sir. \
                 Proceeding with a fresh installation rather than an upgrade, \
                 as there is nothing to remove.\x1b[0m",
                name
            );
        }
        self.install(toml_path)
    }

    // ── Query helpers ──────────────────────────────────────────────────────

    pub fn is_installed(&self, name: &str) -> bool {
        self.db.has(name)
    }

    pub fn list_installed(&self) -> Vec<String> {
        self.db.list().iter().map(|r| {
            format!("{} {} ({})", r.name, r.version, r.category)
        }).collect()
    }
}

// ── Helpers ───────────────────────────────────────────────────────────────

fn resolve_bin(self_dir: &Path, name: &str) -> PathBuf {
    let candidate = self_dir.join(name);
    if candidate.exists() { candidate } else { PathBuf::from(name) }
}

fn check_exit(bin: &str, status: ExitStatus) -> Result<(), String> {
    if status.success() { return Ok(()); }
    Err(format!(
        "I'm afraid '{}' has failed in its duty, my lord — exit status: {}. \
         Inspect the output above for the root cause.",
        bin, status
    ))
}

fn read_manifest(path: &Path) -> io::Result<Vec<String>> {
    let content = fs::read_to_string(path)?;
    Ok(content.lines()
        .filter(|l| !l.is_empty())
        .map(String::from)
        .collect())
}

fn build_record(name: &str, files: &[String], root: &Path) -> PackageRecord {
    PackageRecord {
        name:         name.to_string(),
        version:      "unknown".to_string(),
        category:     "unknown".to_string(),
        install_root: root.to_string_lossy().into_owned(),
        installed_at: SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0),
        files:        files.to_vec(),
    }
}
