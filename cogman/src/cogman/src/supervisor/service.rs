//! Service definition — parsed from /etc/cogman/services/*.service

use std::collections::HashMap;
use std::fs;
use std::path::Path;

#[derive(Debug, Clone, PartialEq)]
pub enum ServiceType { Process, Oneshot, Forking }

#[derive(Debug, Clone, PartialEq)]
pub enum RestartPolicy { Never, OnFailure, Always }

/// How to check if a service is actually healthy (beyond "PID exists").
#[derive(Debug, Clone)]
pub enum HealthProbe {
    /// Connect to localhost:port — success if TCP handshake completes.
    Tcp { port: u16 },
    /// Run a shell command — success if exit code is 0.
    Exec { command: String },
    /// HTTP GET to localhost:port/path — success if status < 400.
    Http { port: u16, path: String },
}

#[derive(Debug, Clone)]
pub struct HealthConfig {
    pub probe:    HealthProbe,
    pub interval: u64,   // seconds between checks
    pub timeout:  u64,   // seconds before probe is considered failed
    pub retries:  u32,   // consecutive failures before restart
}

#[derive(Debug, Clone)]
pub struct ServiceDef {
    pub name:          String,
    pub command:       String,
    pub svc_type:      ServiceType,
    pub restart:       RestartPolicy,
    pub restart_delay: u64,
    pub depends:       Vec<String>,
    pub env:           HashMap<String, String>,
    pub health:        Option<HealthConfig>,
    /// Landlock write paths (empty = no restriction)
    pub allow_write:   Vec<String>,
    /// Landlock read-only paths (empty = inherit)
    pub allow_read:    Vec<String>,
}

impl Default for ServiceDef {
    fn default() -> Self {
        ServiceDef {
            name:          String::new(),
            command:       String::new(),
            svc_type:      ServiceType::Process,
            restart:       RestartPolicy::Never,
            restart_delay: 1,
            depends:       Vec::new(),
            env:           HashMap::new(),
            health:        None,
            allow_write:   Vec::new(),
            allow_read:    Vec::new(),
        }
    }
}

// ── Parser ────────────────────────────────────────────────────────────────

impl ServiceDef {
    pub fn load_dir(dir: &Path) -> Vec<ServiceDef> {
        let Ok(entries) = fs::read_dir(dir) else { return Vec::new() };
        let mut svcs = Vec::new();
        let mut paths: Vec<_> = entries
            .filter_map(|e| e.ok())
            .filter(|e| e.path().extension().map_or(false, |x| x == "service"))
            .map(|e| e.path())
            .collect();
        paths.sort();
        for p in paths {
            match Self::parse_file(&p) {
                Ok(s) => {
                    eprintln!("cogman: loaded service '{}' from {}", s.name, p.display());
                    svcs.push(s);
                }
                Err(e) => eprintln!("cogman: skip {} — {}", p.display(), e),
            }
        }
        svcs
    }

    pub fn parse_file(path: &Path) -> Result<ServiceDef, String> {
        let src = fs::read_to_string(path)
            .map_err(|e| format!("read: {e}"))?;
        Self::parse_str(&src)
    }

    pub fn parse_str(src: &str) -> Result<ServiceDef, String> {
        let mut svc = ServiceDef::default();
        let mut section = String::new();

        for raw in src.lines() {
            let line = raw.trim();
            if line.is_empty() || line.starts_with('#') { continue; }

            if line.starts_with('[') && line.ends_with(']') {
                section = line[1..line.len()-1].to_lowercase();
                continue;
            }

            let (key, val) = line.split_once('=')
                .map(|(k,v)|(k.trim(),v.trim()))
                .ok_or_else(|| format!("bad line: {line}"))?;

            match section.as_str() {
                "service" => Self::apply_service_kv(&mut svc, key, val)?,
                "env"     => { svc.env.insert(key.to_string(), val.to_string()); }
                "health"  => Self::apply_health_kv(&mut svc, key, val)?,
                "policy"  => Self::apply_policy_kv(&mut svc, key, val)?,
                _         => {}
            }
        }

        if svc.name.is_empty() {
            return Err("missing name".into());
        }
        if svc.command.is_empty() {
            return Err("missing command".into());
        }
        Ok(svc)
    }

    fn apply_service_kv(svc: &mut ServiceDef, k: &str, v: &str) -> Result<(), String> {
        match k {
            "name"          => svc.name = v.into(),
            "command"       => svc.command = v.into(),
            "type"          => svc.svc_type = match v {
                "oneshot"  => ServiceType::Oneshot,
                "forking"  => ServiceType::Forking,
                _          => ServiceType::Process,
            },
            "restart"       => svc.restart = match v {
                "always"     => RestartPolicy::Always,
                "on-failure" => RestartPolicy::OnFailure,
                _            => RestartPolicy::Never,
            },
            "restart_delay" => svc.restart_delay = v.parse().unwrap_or(1),
            "depends"       => {
                svc.depends = v.split(',')
                    .map(str::trim)
                    .filter(|s| !s.is_empty())
                    .map(String::from)
                    .collect();
            }
            _ => {}
        }
        Ok(())
    }

    fn apply_health_kv(svc: &mut ServiceDef, k: &str, v: &str) -> Result<(), String> {
        let hc = svc.health.get_or_insert(HealthConfig {
            probe:    HealthProbe::Exec { command: "true".into() },
            interval: 10,
            timeout:  3,
            retries:  3,
        });
        match k {
            "type" => match v {
                "tcp"  => hc.probe = HealthProbe::Tcp { port: 80 },
                "http" => hc.probe = HealthProbe::Http { port: 80, path: "/".into() },
                "exec" => hc.probe = HealthProbe::Exec { command: "true".into() },
                other  => return Err(format!("unknown health type: {other}")),
            },
            "port" => match &mut hc.probe {
                HealthProbe::Tcp  { port } => *port = v.parse().unwrap_or(80),
                HealthProbe::Http { port, .. } => *port = v.parse().unwrap_or(80),
                _ => {}
            },
            "path" => if let HealthProbe::Http { path, .. } = &mut hc.probe {
                *path = v.into();
            },
            "command" => if let HealthProbe::Exec { command } = &mut hc.probe {
                *command = v.into();
            },
            "interval" => hc.interval = v.parse().unwrap_or(10),
            "timeout"  => hc.timeout  = v.parse().unwrap_or(3),
            "retries"  => hc.retries  = v.parse().unwrap_or(3),
            _ => {}
        }
        Ok(())
    }

    fn apply_policy_kv(svc: &mut ServiceDef, k: &str, v: &str) -> Result<(), String> {
        let paths: Vec<String> = v.split(',')
            .map(str::trim)
            .filter(|s| !s.is_empty())
            .map(String::from)
            .collect();
        match k {
            "allow_write" => svc.allow_write = paths,
            "allow_read"  => svc.allow_read  = paths,
            _ => {}
        }
        Ok(())
    }
}
