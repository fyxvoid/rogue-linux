/*
 * cogman/src/planner/variants/binary.rs - Binary Deployment Strategy
 *
 * This file implements the "Binary" installation variant, which 
 * focuses on direct artifact deployment from pre-built archives.
 *
 * Why: To provide a fast, compilation-free path for system updates 
 * and tool injection.
 */

use crate::metadata::PackageMetadata;
use crate::plan::layout::{PlanStep, StepOp, FailPolicy};

/// Generate execution steps for the binary install variant.
/// Sequence: mkdir → extract → verify → copy.
pub fn plan(meta: &PackageMetadata, rootfs: &str, metadata_root: &std::path::Path) -> Vec<PlanStep> {
    let name = &meta.identity.name;
    let cat = &meta.identity.category;
    let src = &meta.identity.source.file;
    let pkgroot = format!("{}/pkgroot/{}", rootfs, name);
    
    // Absolute path to the source tarball
    let tar_path = metadata_root.join("packages").join(cat).join(name).join("tar").join(src);
    let tar_str = tar_path.to_string_lossy();

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
        command: format!("tar -xf {} -C {}", tar_str, pkgroot),
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
