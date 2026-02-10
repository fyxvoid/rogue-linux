#![allow(dead_code)]
// cogman planner — tmp/lifecycle.rs
// Lifecycle management for /tmp/cogman-build-*.
// strict lifecycle that must be encoded correctly into the plan:
//   create → build → verify → install → cleanup
//
// If any phase is missing or mis-ordered, the executor will produce
// incorrect results. This module makes the lifecycle explicit.

/// Describes the lifecycle of a temporary build directory.
/// Used by variants/native.rs to encode the correct step sequence.
pub struct TmpLifecycle {
    pub path: String,
    pub keep: bool,
}

impl TmpLifecycle {
    /// Create a new lifecycle for a package's temporary build directory.
    pub fn for_package(name: &str) -> Self {
        Self {
            path: format!("/tmp/cogman-build-{}", name),
            keep: false,
        }
    }

    /// Mark this lifecycle to preserve the directory (--keep-tmp).
    pub fn preserve(&mut self) {
        self.keep = true;
    }

    /// Should the cleanup step be emitted?
    pub fn should_cleanup(&self) -> bool {
        !self.keep
    }
}
