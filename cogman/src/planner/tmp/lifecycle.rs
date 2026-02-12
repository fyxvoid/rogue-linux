#![allow(dead_code)]
/*
 * cogman/src/planner/tmp/lifecycle.rs - Build Workspace Lifecycle
 *
 * This file implements the explicit state transitions for temporary 
 * build directories (create -> build -> verify -> install -> cleanup).
 *
 * Why: To guarantee that filesystem state remains consistent even 
 * across complex, multi-stage native builds.
 */

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
