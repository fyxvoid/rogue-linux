//! Process supervisor — Rust rewrite of cogman/src/supervisor/
//!
//! Runs the healing loop: spawn → watch → restart on death.
//! Health checks run in a dedicated thread per service.
//! Landlock policy applied in child before exec.

pub mod service;

use service::{ServiceDef, ServiceType, RestartPolicy, HealthProbe};
use crate::policy;

use std::io::{Read, Write};
use std::net::TcpStream;
use std::os::unix::process::CommandExt;
use std::path::Path;
use std::process::Command;
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

// ── Service runtime state ─────────────────────────────────────────────────

#[derive(Debug, Clone, PartialEq)]
pub enum ServiceState {
    Pending,      // waiting for deps
    Starting,
    Running,
    Stopping,
    Stopped,      // explicit stop, no auto-restart
    Restarting { at: Instant },
    Failed,
    Done,         // oneshot completed successfully
}

pub struct ServiceEntry {
    pub def:           ServiceDef,
    pub state:         ServiceState,
    pub pid:           Option<u32>,
    pub started_at:    Option<Instant>,
    pub restart_count: u32,
    pub exit_code:     Option<i32>,
    /// Consecutive health-check failures
    pub health_fails:  u32,
}

impl ServiceEntry {
    fn new(def: ServiceDef) -> Self {
        ServiceEntry {
            def,
            state:         ServiceState::Pending,
            pid:           None,
            started_at:    None,
            restart_count: 0,
            exit_code:     None,
            health_fails:  0,
        }
    }
}

// ── Supervisor ────────────────────────────────────────────────────────────

pub struct Supervisor {
    pub services: Arc<Mutex<Vec<ServiceEntry>>>,
}

impl Supervisor {
    pub fn new() -> Self {
        Supervisor {
            services: Arc::new(Mutex::new(Vec::new())),
        }
    }

    pub fn load_dir(&self, dir: &Path) {
        let defs = ServiceDef::load_dir(dir);
        let mut svcs = self.services.lock().unwrap();
        for d in defs {
            svcs.push(ServiceEntry::new(d));
        }
        eprintln!("\x1b[96mI have prepared {} service(s) for your consideration, sir.\x1b[0m", svcs.len());
    }

    /// Main supervision loop. Runs forever (call from a dedicated thread).
    pub fn run(&self) {
        // Initial start pass
        self.start_ready();

        loop {
            self.reap_dead();
            self.tick_restarts();
            self.start_ready();
            self.run_health_checks();
            std::thread::sleep(Duration::from_millis(200));
        }
    }

    // ── Spawn ─────────────────────────────────────────────────────────────

    pub fn spawn_service(entry: &mut ServiceEntry) -> bool {
        let def = &entry.def;
        eprintln!("\x1b[96mAttending to '{}', sir.\x1b[0m", def.name);

        // Build Command; Landlock + env applied via pre_exec
        let read_paths  = def.allow_read.clone();
        let write_paths = def.allow_write.clone();

        let mut cmd = Command::new("/bin/sh");
        cmd.arg("-c").arg(&def.command);
        for (k, v) in &def.env {
            cmd.env(k, v);
        }

        // Apply Landlock in child before exec (only if policy is set)
        if !read_paths.is_empty() || !write_paths.is_empty() {
            unsafe {
                cmd.pre_exec(move || {
                    match policy::apply(&read_paths, &write_paths) {
                        Ok(_)  => Ok(()),
                        Err(e) => {
                            eprintln!("[{}] policy: {e}", "svc");
                            Ok(()) // non-fatal: log and continue
                        }
                    }
                });
            }
        }

        match cmd.spawn() {
            Ok(child) => {
                eprintln!("\x1b[92m'{}' is now in service, sir. (pid={})\x1b[0m", def.name, child.id());
                entry.pid        = Some(child.id());
                entry.state      = ServiceState::Running;
                entry.started_at = Some(Instant::now());
                // Detach child — we'll poll via waitpid
                std::mem::forget(child);
                true
            }
            Err(e) => {
                eprintln!("\x1b[91mRegrettably, '{}' has failed to take to its post, sir: {e}\x1b[0m", def.name);
                entry.state = ServiceState::Failed;
                false
            }
        }
    }

    // ── Reap dead children ────────────────────────────────────────────────

    fn reap_dead(&self) {
        let mut svcs = self.services.lock().unwrap();
        for entry in svcs.iter_mut() {
            let Some(pid) = entry.pid else { continue };
            if entry.state != ServiceState::Running &&
               entry.state != ServiceState::Starting { continue; }

            // Non-blocking waitpid
            let mut status: libc::c_int = 0;
            let ret = unsafe { libc::waitpid(pid as libc::pid_t, &mut status, libc::WNOHANG) };

            if ret == 0 { continue; } // still alive

            // Process exited
            let code = if libc::WIFEXITED(status)  { libc::WEXITSTATUS(status) }
                       else if libc::WIFSIGNALED(status) { -(libc::WTERMSIG(status)) }
                       else { -1 };

            eprintln!("\x1b[93m'{}' has stood down, sir. (pid={pid}, exit={code})\x1b[0m", entry.def.name);
            entry.pid       = None;
            entry.exit_code = Some(code);
            entry.health_fails = 0;

            Self::apply_restart_policy(entry, code);
        }
    }

    fn apply_restart_policy(entry: &mut ServiceEntry, exit_code: i32) {
        // Oneshot: done on success, failed otherwise
        if entry.def.svc_type == ServiceType::Oneshot {
            entry.state = if exit_code == 0 { ServiceState::Done } else { ServiceState::Failed };
            return;
        }
        // Forking: parent exit is intentional
        if entry.def.svc_type == ServiceType::Forking {
            entry.state = ServiceState::Done;
            return;
        }
        // Explicit stop — do not restart
        if entry.state == ServiceState::Stopping || entry.state == ServiceState::Stopped {
            entry.state = ServiceState::Stopped;
            return;
        }

        let should_restart = match entry.def.restart {
            RestartPolicy::Always    => true,
            RestartPolicy::OnFailure => exit_code != 0,
            RestartPolicy::Never     => false,
        };

        if should_restart {
            let delay = Duration::from_secs(entry.def.restart_delay);
            eprintln!("\x1b[96m'{}' shall return to duty in {}s, sir.\x1b[0m", entry.def.name, entry.def.restart_delay);
            entry.state = ServiceState::Restarting { at: Instant::now() + delay };
        } else {
            entry.state = ServiceState::Stopped;
        }
    }

    // ── Restart tick ──────────────────────────────────────────────────────

    fn tick_restarts(&self) {
        let mut svcs = self.services.lock().unwrap();
        let now = Instant::now();
        for entry in svcs.iter_mut() {
            if let ServiceState::Restarting { at } = entry.state {
                if now >= at {
                    entry.restart_count += 1;
                    eprintln!("\x1b[96mReturning '{}' to duty, sir. (attempt {})\x1b[0m",
                              entry.def.name, entry.restart_count);
                    Self::spawn_service(entry);
                }
            }
        }
    }

    // ── Start services whose deps are satisfied ───────────────────────────

    fn start_ready(&self) {
        let mut svcs = self.services.lock().unwrap();

        // Collect which services are satisfied (Running or Done)
        let satisfied: Vec<String> = svcs.iter()
            .filter(|e| matches!(e.state, ServiceState::Running | ServiceState::Done))
            .map(|e| e.def.name.clone())
            .collect();

        for entry in svcs.iter_mut() {
            if entry.state != ServiceState::Pending { continue; }
            // Never started (started_at == None) AND deps met
            if entry.started_at.is_some() { continue; }

            let deps_met = entry.def.depends.iter()
                .all(|d| satisfied.contains(d));
            if !deps_met { continue; }

            Self::spawn_service(entry);
        }
    }

    // ── Health checks ─────────────────────────────────────────────────────

    fn run_health_checks(&self) {
        let mut svcs = self.services.lock().unwrap();
        for entry in svcs.iter_mut() {
            if entry.state != ServiceState::Running { continue; }
            let Some(ref hc) = entry.def.health.clone() else { continue };

            // Simple interval: only check once per `interval` seconds
            // (track via health_fails as a proxy — real impl would use last_check time)
            let ok = run_probe(&hc.probe, hc.timeout);
            if ok {
                entry.health_fails = 0;
            } else {
                entry.health_fails += 1;
                eprintln!("\x1b[93m'{}' appears to be feeling rather unwell, sir. ({}/{})\x1b[0m",
                          entry.def.name, entry.health_fails, hc.retries);

                if entry.health_fails >= hc.retries {
                    eprintln!("\x1b[91mI'm afraid '{}' has exceeded its health threshold, sir — recalling it for remediation.\x1b[0m", entry.def.name);
                    if let Some(pid) = entry.pid {
                        unsafe { libc::kill(pid as libc::pid_t, libc::SIGTERM); }
                    }
                    entry.health_fails = 0;
                }
            }
        }
    }

    // ── Control interface ─────────────────────────────────────────────────

    pub fn ctl_stop(&self, name: &str) -> Result<(), String> {
        let mut svcs = self.services.lock().unwrap();
        let entry = svcs.iter_mut().find(|e| e.def.name == name)
            .ok_or_else(|| format!(
                "'{}' is not on my roster, sir. Perhaps check the spelling?",
                name
            ))?;

        if matches!(entry.state, ServiceState::Stopped | ServiceState::Done) {
            return Err(format!(
                "'{}' is not currently running, sir. \
                 Stopping something that has already stopped is, \
                 with respect, a somewhat futile endeavour.",
                name
            ));
        }
        entry.state = ServiceState::Stopping;
        if let Some(pid) = entry.pid {
            unsafe { libc::kill(pid as libc::pid_t, libc::SIGTERM); }
        }
        entry.pid   = None;
        entry.state = ServiceState::Stopped;
        Ok(())
    }

    pub fn ctl_start(&self, name: &str) -> Result<(), String> {
        let mut svcs = self.services.lock().unwrap();
        let entry = svcs.iter_mut().find(|e| e.def.name == name)
            .ok_or_else(|| format!(
                "'{}' is not on my roster, sir. It either has not been loaded \
                 or the name is misspelled. \
                 Might I suggest checking '/etc/cogman/services' for the correct designation?",
                name
            ))?;

        if matches!(entry.state, ServiceState::Running | ServiceState::Starting) {
            return Err(format!(
                "'{}' is already running quite contentedly, sir. \
                 Starting it again would accomplish very little. \
                 If a restart was intended, 'cogman svc restart {}' is the order you seek.",
                name, name
            ));
        }
        entry.state = ServiceState::Pending;
        entry.started_at = None;
        Ok(())
    }

    pub fn ctl_restart(&self, name: &str) -> Result<(), String> {
        self.ctl_stop(name).ok(); // ignore if already stopped — restart is always valid
        let mut svcs = self.services.lock().unwrap();
        let entry = svcs.iter_mut().find(|e| e.def.name == name)
            .ok_or_else(|| format!(
                "'{}' is not on my roster, sir. I cannot restart what I have never managed.",
                name
            ))?;
        entry.state      = ServiceState::Pending;
        entry.started_at = None;
        Ok(())
    }

    pub fn ctl_status(&self, name: &str) -> Result<String, String> {
        let svcs = self.services.lock().unwrap();
        let entry = svcs.iter().find(|e| e.def.name == name)
            .ok_or_else(|| format!(
                "'{}' is not on my roster, sir. \
                 I have no record of a service by that name. \
                 Perhaps 'cogman svc list' would help identify the correct designation?",
                name
            ))?;
        Ok(format_status(entry))
    }

    pub fn ctl_list(&self) -> String {
        let svcs = self.services.lock().unwrap();
        if svcs.is_empty() {
            return "The service roster is completely empty, sir. No services have been loaded.\n\
                    Might I suggest populating '/etc/cogman/services' with some definitions?\n".into();
        }
        let mut out = format!("The following {} service(s) are under my supervision, sir:\n\n", svcs.len());
        for e in svcs.iter() {
            let state_str = state_label(&e.state);
            let pid_str   = e.pid.map_or("—".into(), |p| p.to_string());
            out.push_str(&format!(
                "  {:<24} {:<14} pid={:<8} restarts={}\n",
                e.def.name, state_str, pid_str, e.restart_count
            ));
        }
        out
    }
}

// ── Health probe runners ──────────────────────────────────────────────────

fn run_probe(probe: &HealthProbe, timeout_secs: u64) -> bool {
    let timeout = Duration::from_secs(timeout_secs);
    match probe {
        HealthProbe::Tcp { port } => {
            let addr = format!("127.0.0.1:{port}");
            TcpStream::connect_timeout(
                &addr.parse().unwrap_or("127.0.0.1:80".parse().unwrap()),
                timeout,
            ).is_ok()
        }
        HealthProbe::Http { port, path } => {
            let addr = format!("127.0.0.1:{port}");
            let Ok(mut stream) = TcpStream::connect_timeout(
                &addr.parse().unwrap_or("127.0.0.1:80".parse().unwrap()),
                timeout,
            ) else { return false };
            let req = format!("GET {path} HTTP/1.0\r\nHost: localhost\r\n\r\n");
            if stream.write_all(req.as_bytes()).is_err() { return false; }
            let mut resp = String::new();
            if stream.read_to_string(&mut resp).is_err() { return false; }
            // Success if HTTP status < 400
            resp.starts_with("HTTP/") &&
            resp.split_whitespace().nth(1)
                .and_then(|s| s.parse::<u16>().ok())
                .map_or(false, |code| code < 400)
        }
        HealthProbe::Exec { command } => {
            std::process::Command::new("/bin/sh")
                .arg("-c")
                .arg(command)
                .stdin(std::process::Stdio::null())
                .stdout(std::process::Stdio::null())
                .stderr(std::process::Stdio::null())
                .status()
                .map_or(false, |s| s.success())
        }
    }
}

// ── Formatting helpers ────────────────────────────────────────────────────

fn state_label(s: &ServiceState) -> &'static str {
    match s {
        ServiceState::Pending    => "pending",
        ServiceState::Starting   => "starting",
        ServiceState::Running    => "running",
        ServiceState::Stopping   => "stopping",
        ServiceState::Stopped    => "stopped",
        ServiceState::Restarting { .. } => "restarting",
        ServiceState::Failed     => "failed",
        ServiceState::Done       => "done",
    }
}

fn format_status(e: &ServiceEntry) -> String {
    let state = state_label(&e.state);
    let pid   = e.pid.map_or("none".into(), |p| p.to_string());
    let commentary = match e.state {
        ServiceState::Running  => "in fine fettle, sir.",
        ServiceState::Failed   => "I'm afraid this one has let us down, sir.",
        ServiceState::Stopped  => "stood down at your instruction, sir.",
        ServiceState::Done     => "completed its duties and retired gracefully, sir.",
        ServiceState::Pending  => "awaiting its dependencies, sir. Patience.",
        ServiceState::Restarting { .. } => "gathering itself for another attempt, sir.",
        ServiceState::Starting => "coming to attention, sir.",
        ServiceState::Stopping => "in the process of standing down, sir.",
    };
    format!(
        "Service Report — '{}'\n\
         ─────────────────────────────\n\
         State:        {} ({})\n\
         PID:          {}\n\
         Type:         {:?}\n\
         Restart:      {:?}\n\
         Restarts:     {}\n\
         Last Exit:    {}\n\
         Health Fails: {}\n",
        e.def.name,
        state, commentary,
        pid,
        e.def.svc_type,
        e.def.restart,
        e.restart_count,
        e.exit_code.unwrap_or(0),
        e.health_fails,
    )
}
