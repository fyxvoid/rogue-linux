//! Unix-socket control server (daemon side) and client helper.
//!
//! Protocol: newline-terminated text frames.
//!   Request:  "<verb> [arg]\n"
//!   Response: "OK\n<payload>" | "ERR <message>\n"
//!
//! Verbs:
//!   LIST
//!   STATUS <name>
//!   START  <name>
//!   STOP   <name>
//!   RESTART <name>
//!   PING

use std::io::{BufRead, BufReader, Write};
use std::os::unix::net::{UnixListener, UnixStream};
use std::path::Path;
use std::sync::Arc;
use std::time::Duration;

use crate::supervisor::Supervisor;

pub const SOCK_PATH: &str = "/run/cogman.sock";

// ── Server ────────────────────────────────────────────────────────────────

/// Bind the control socket and serve requests in a loop (blocking).
/// Call from a dedicated thread.
pub fn serve(sock_path: &Path, sup: Arc<Supervisor>) {
    // Remove stale socket
    let _ = std::fs::remove_file(sock_path);

    let listener = match UnixListener::bind(sock_path) {
        Ok(l)  => l,
        Err(e) => { eprintln!("\x1b[91mI'm afraid the control socket could not be established, sir ({}): {e}\x1b[0m", sock_path.display()); return; }
    };
    eprintln!("\x1b[96mThe control post is open and awaiting your orders, sir. ({})\x1b[0m", sock_path.display());

    for stream in listener.incoming() {
        match stream {
            Ok(s)  => handle_client(s, Arc::clone(&sup)),
            Err(e) => eprintln!("cogman/ctl: accept: {e}"),
        }
    }
}

fn handle_client(stream: UnixStream, sup: Arc<Supervisor>) {
    let mut writer = match stream.try_clone() {
        Ok(w)  => w,
        Err(_) => return,
    };
    let reader = BufReader::new(stream);

    for line in reader.lines() {
        let line = match line {
            Ok(l)  => l,
            Err(_) => break,
        };
        let response = dispatch(line.trim(), &sup);
        let _ = writer.write_all(response.as_bytes());
    }
}

fn dispatch(cmd: &str, sup: &Supervisor) -> String {
    let mut parts = cmd.splitn(2, ' ');
    let verb = parts.next().unwrap_or("").to_ascii_uppercase();
    let arg  = parts.next().unwrap_or("").trim();

    match verb.as_str() {
        "PING" => {
            "OK\nAt your service, sir. Cogman is standing by, alert and ready.\n".to_string()
        }
        "LIST" => {
            format!("OK\n{}", sup.ctl_list())
        }
        "STATUS" => {
            if arg.is_empty() {
                return "ERR You haven't told me which service to report on, sir. \
                        Please supply a service name after 'status'.\n".to_string();
            }
            match sup.ctl_status(arg) {
                Ok(s)  => format!("OK\n{s}"),
                Err(e) => format!("ERR {e}\n"),
            }
        }
        "START" => {
            if arg.is_empty() {
                return "ERR Forgive me, sir, but I need to know which service \
                        you'd like me to start. Please provide a name.\n".to_string();
            }
            match sup.ctl_start(arg) {
                Ok(())  => format!("OK\nVery good, sir. '{}' is being brought to attention.\n", arg),
                Err(e)  => format!("ERR {e}\n"),
            }
        }
        "STOP" => {
            if arg.is_empty() {
                return "ERR I'd be delighted to stop a service, sir, \
                        but you haven't told me which one.\n".to_string();
            }
            match sup.ctl_stop(arg) {
                Ok(())  => format!("OK\nVery good, sir. '{}' has been stood down as requested.\n", arg),
                Err(e)  => format!("ERR {e}\n"),
            }
        }
        "RESTART" => {
            if arg.is_empty() {
                return "ERR A restart requires a service name, sir. \
                        I cannot restart everything at once — \
                        that would be somewhat chaotic.\n".to_string();
            }
            match sup.ctl_restart(arg) {
                Ok(())  => format!(
                    "OK\nOf course, sir. '{}' shall be stood down and returned to duty presently.\n",
                    arg
                ),
                Err(e)  => format!("ERR {e}\n"),
            }
        }
        other => {
            format!(
                "ERR '{}' is not a recognised order, sir. \
                 I've served many masters, and not one has ever issued that instruction. \
                 Valid orders are: LIST, STATUS, START, STOP, RESTART, PING.\n",
                other
            )
        }
    }
}

// ── Client ────────────────────────────────────────────────────────────────

/// Send a single command to the running daemon and return the response text.
pub fn send(sock_path: &Path, cmd: &str) -> Result<String, String> {
    let mut stream = UnixStream::connect(sock_path)
        .map_err(|e| format!("connect {}: {e}", sock_path.display()))?;
    stream.set_read_timeout(Some(Duration::from_secs(5)))
        .map_err(|e| format!("set_read_timeout: {e}"))?;

    let msg = format!("{cmd}\n");
    stream.write_all(msg.as_bytes())
        .map_err(|e| format!("write: {e}"))?;

    // Read until EOF
    let mut resp = String::new();
    let mut reader = BufReader::new(&stream);
    loop {
        let mut line = String::new();
        match reader.read_line(&mut line) {
            Ok(0) => break,
            Ok(_) => resp.push_str(&line),
            Err(_) => break,
        }
    }
    Ok(resp)
}

/// Parse the response: strip "OK\n" prefix, return payload; or Err if "ERR …".
pub fn parse_response(raw: &str) -> Result<&str, String> {
    if let Some(rest) = raw.strip_prefix("OK\n") {
        Ok(rest)
    } else if let Some(msg) = raw.strip_prefix("ERR ") {
        Err(msg.trim_end().to_string())
    } else {
        Err(format!("unexpected response: {raw:?}"))
    }
}
