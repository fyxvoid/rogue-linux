// cogmanII planner — variants/binary.rs
// This module exists because the binary install variant is the fastest
// path: extract prebuilt artifacts and copy them into the rootfs.
// No compilation, no temporary directories, no environment injection.

use crate::metadata::PackageMetadata;
use crate::plan::layout::{PlanStep, StepOp, FailPolicy};

/// Generate execution steps for the binary install variant.
/// Sequence: mkdir → extract → verify → copy.
pub fn plan(meta: &PackageMetadata, rootfs: &str) -> Vec<PlanStep> {
    let name = &meta.identity.name;
    let src = &meta.identity.source.file;
    let pkgroot = format!("{}/pkgroot/{}", rootfs, name);

    let mut steps = Vec::new();

    // Create pkgroot directory
    steps.push(PlanStep {
        op: StepOp::Mkdir,
        command: pkgroot.clone(),
        workdir: rootfs.to_string(),
        env: Vec::new(),
        fail_policy: FailPolicy::Abort,
    });

    // Extract prebuilt archive into pkgroot
    steps.push(PlanStep {
        op: StepOp::Exec,
        command: format!("tar -xf tar/{} -C {}", src, pkgroot),
        workdir: rootfs.to_string(),
        env: Vec::new(),
        fail_policy: FailPolicy::Abort,
    });

    // Verify extraction (if verify section present)
    if let Some(ref verify) = meta.installer.verify {
        for f in &verify.expected_files {
            steps.push(PlanStep {
                op: StepOp::Verify,
                command: format!("{}/{}", pkgroot, f),
                workdir: rootfs.to_string(),
                env: Vec::new(),
                fail_policy: FailPolicy::Abort,
            });
        }
    }

    // Copy into final rootfs
    steps.push(PlanStep {
        op: StepOp::Copy,
        command: format!("{}|{}", pkgroot, rootfs),
        workdir: rootfs.to_string(),
        env: Vec::new(),
        fail_policy: FailPolicy::Abort,
    });

    steps
}
