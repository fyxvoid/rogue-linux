//! Runtime Landlock filesystem isolation.
//!
//! Called in the child process immediately before execve(), after fork().
//! If Landlock is unavailable (old kernel), falls back gracefully to no-op.
//!
//! Landlock requires Linux ≥ 5.13. On your Rust kernel, make sure
//! CONFIG_SECURITY_LANDLOCK=y.

use std::ffi::CString;
use libc::{c_int, c_uint, c_long};

// ── Landlock ABI constants (from linux/landlock.h) ────────────────────────

const LANDLOCK_CREATE_RULESET:          c_long = 444;
const LANDLOCK_ADD_RULE:                c_long = 445;
const LANDLOCK_RESTRICT_SELF:           c_long = 446;

const LANDLOCK_RULESET_ATTR_SIZE:       usize  = 4;

const LANDLOCK_ACCESS_FS_EXECUTE:       u64 = 1 << 0;
const LANDLOCK_ACCESS_FS_WRITE_FILE:    u64 = 1 << 1;
const LANDLOCK_ACCESS_FS_READ_FILE:     u64 = 1 << 2;
const LANDLOCK_ACCESS_FS_READ_DIR:      u64 = 1 << 3;
const LANDLOCK_ACCESS_FS_REMOVE_DIR:    u64 = 1 << 4;
const LANDLOCK_ACCESS_FS_REMOVE_FILE:   u64 = 1 << 5;
const LANDLOCK_ACCESS_FS_MAKE_CHAR:     u64 = 1 << 6;
const LANDLOCK_ACCESS_FS_MAKE_DIR:      u64 = 1 << 7;
const LANDLOCK_ACCESS_FS_MAKE_REG:      u64 = 1 << 8;
const LANDLOCK_ACCESS_FS_MAKE_SOCK:     u64 = 1 << 9;
const LANDLOCK_ACCESS_FS_MAKE_FIFO:     u64 = 1 << 10;
const LANDLOCK_ACCESS_FS_MAKE_BLOCK:    u64 = 1 << 11;
const LANDLOCK_ACCESS_FS_MAKE_SYM:      u64 = 1 << 12;

const LANDLOCK_RULE_PATH_BENEATH:       c_uint = 1;

const ALL_FS_ACCESS: u64 =
    LANDLOCK_ACCESS_FS_EXECUTE     | LANDLOCK_ACCESS_FS_WRITE_FILE  |
    LANDLOCK_ACCESS_FS_READ_FILE   | LANDLOCK_ACCESS_FS_READ_DIR    |
    LANDLOCK_ACCESS_FS_REMOVE_DIR  | LANDLOCK_ACCESS_FS_REMOVE_FILE |
    LANDLOCK_ACCESS_FS_MAKE_CHAR   | LANDLOCK_ACCESS_FS_MAKE_DIR    |
    LANDLOCK_ACCESS_FS_MAKE_REG    | LANDLOCK_ACCESS_FS_MAKE_SOCK   |
    LANDLOCK_ACCESS_FS_MAKE_FIFO   | LANDLOCK_ACCESS_FS_MAKE_BLOCK  |
    LANDLOCK_ACCESS_FS_MAKE_SYM;

const READ_ONLY_ACCESS: u64 =
    LANDLOCK_ACCESS_FS_READ_FILE | LANDLOCK_ACCESS_FS_READ_DIR |
    LANDLOCK_ACCESS_FS_EXECUTE;

const WRITE_ACCESS: u64 = ALL_FS_ACCESS;

// ── Structs matching kernel ABI ───────────────────────────────────────────

#[repr(C)]
struct LandlockRulesetAttr {
    handled_access_fs: u64,
}

#[repr(C)]
struct LandlockPathBeneathAttr {
    allowed_access: u64,
    parent_fd:      i32,
}

// ── Public API ────────────────────────────────────────────────────────────

/// Apply Landlock restrictions in the current process.
///
/// `read_paths`  — directories/files the process may read.
/// `write_paths` — directories/files the process may write.
///
/// Call this in the child between fork() and exec().
/// Returns Ok(true) if Landlock was applied, Ok(false) if unavailable.
pub fn apply(read_paths: &[String], write_paths: &[String]) -> Result<bool, String> {
    if read_paths.is_empty() && write_paths.is_empty() {
        return Ok(false); // no policy — skip
    }

    // Create ruleset
    let attr = LandlockRulesetAttr { handled_access_fs: ALL_FS_ACCESS };
    let ruleset_fd = unsafe {
        syscall3(
            LANDLOCK_CREATE_RULESET,
            &attr as *const _ as c_long,
            LANDLOCK_RULESET_ATTR_SIZE as c_long,
            0,
        )
    };
    if ruleset_fd < 0 {
        let err = unsafe { *libc::__errno_location() };
        if err == libc::ENOSYS || err == libc::EOPNOTSUPP {
            eprintln!("cogman/policy: Landlock unavailable (kernel too old), skipping");
            return Ok(false);
        }
        return Err(format!("landlock_create_ruleset: errno {err}"));
    }
    let ruleset_fd = ruleset_fd as c_int;

    // Add read-only rules
    for path in read_paths {
        if let Err(e) = add_path_rule(ruleset_fd, path, READ_ONLY_ACCESS) {
            eprintln!("cogman/policy: read rule for '{path}': {e}");
        }
    }

    // Add write rules
    for path in write_paths {
        if let Err(e) = add_path_rule(ruleset_fd, path, WRITE_ACCESS) {
            eprintln!("cogman/policy: write rule for '{path}': {e}");
        }
    }

    // Raise the "no new privileges" bit (required by Landlock)
    let ret = unsafe { libc::prctl(libc::PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) };
    if ret != 0 {
        unsafe { libc::close(ruleset_fd) };
        return Err(format!("prctl(NO_NEW_PRIVS): {ret}"));
    }

    // Restrict self
    let ret = unsafe {
        syscall3(LANDLOCK_RESTRICT_SELF, ruleset_fd as c_long, 0, 0)
    };
    unsafe { libc::close(ruleset_fd) };
    if ret != 0 {
        return Err(format!("landlock_restrict_self: errno {}", unsafe { *libc::__errno_location() }));
    }

    Ok(true)
}

fn add_path_rule(ruleset_fd: c_int, path: &str, access: u64) -> Result<(), String> {
    let cpath = CString::new(path)
        .map_err(|_| format!("nul in path: {path}"))?;

    let fd = unsafe {
        libc::open(cpath.as_ptr(), libc::O_PATH | libc::O_CLOEXEC)
    };
    if fd < 0 {
        return Err(format!("open O_PATH '{}': errno {}", path, unsafe { *libc::__errno_location() }));
    }

    let rule = LandlockPathBeneathAttr { allowed_access: access, parent_fd: fd };
    let ret = unsafe {
        syscall3(
            LANDLOCK_ADD_RULE,
            ruleset_fd as c_long,
            LANDLOCK_RULE_PATH_BENEATH as c_long,
            &rule as *const _ as c_long,
        )
    };
    unsafe { libc::close(fd) };

    if ret != 0 {
        Err(format!("landlock_add_rule: errno {}", unsafe { *libc::__errno_location() }))
    } else {
        Ok(())
    }
}

unsafe fn syscall3(nr: c_long, a: c_long, b: c_long, c: c_long) -> c_long {
    libc::syscall(nr, a, b, c)
}
