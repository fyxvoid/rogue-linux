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
use crate::metadata::schema::SourceKind;
use crate::plan::layout::{PlanStep, StepOp, FailPolicy};

/// Generate execution steps for the binary install variant.
/// For packages with a real source (tarball/git): mkdir → extract → verify → copy.
/// For packages with kind=none/local: run installer steps directly as OP_EXEC.
pub fn plan(meta: &PackageMetadata, rootfs: &str, metadata_root: &std::path::Path) -> Vec<PlanStep> {
    let name = &meta.identity.name;
    let cat = &meta.identity.category;
    let kind = meta.identity.source.kind;
    let pkgroot = format!("{}/pkgroot/{}", rootfs, name);

    let mut steps = Vec::new();

    match kind {
        SourceKind::None | SourceKind::Local => {
            // No source archive — run installer steps directly.
            for cmd in &meta.installer.steps {
                steps.push(PlanStep {
                    op: StepOp::Exec,
                    command: cmd.clone(),
                    workdir: rootfs.to_string(),
                    env: Vec::new(),
                    fail_policy: FailPolicy::Abort,
                });
            }
        }
        SourceKind::Tarball | SourceKind::Git => {
            let src = meta.identity.source.file.as_deref().unwrap_or("");
            let tar_path = metadata_root.join("packages").join(cat).join(name).join("tar").join(src);
            let tar_str = tar_path.to_string_lossy();

            steps.push(PlanStep {
                op: StepOp::Mkdir,
                command: pkgroot.clone(),
                workdir: rootfs.to_string(),
                env: Vec::new(),
                fail_policy: FailPolicy::Abort,
            });

            steps.push(PlanStep {
                op: StepOp::Exec,
                command: format!("tar -xf {} -C {}", tar_str, pkgroot),
                workdir: rootfs.to_string(),
                env: Vec::new(),
                fail_policy: FailPolicy::Abort,
            });

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

            steps.push(PlanStep {
                op: StepOp::Copy,
                command: format!("{}|{}", pkgroot, rootfs),
                workdir: rootfs.to_string(),
                env: Vec::new(),
                fail_policy: FailPolicy::Abort,
            });

            // Append installer steps after copy.
            for cmd in &meta.installer.steps {
                steps.push(PlanStep {
                    op: StepOp::Exec,
                    command: cmd.clone(),
                    workdir: rootfs.to_string(),
                    env: Vec::new(),
                    fail_policy: FailPolicy::Abort,
                });
            }
        }
    }

    steps
}

/// Generate steps for the uninstall variant.
/// Writes an uninstaller shell script to /var/lib/cogman/uninstallers/<name>.sh
/// and then runs the explicit [uninstaller] steps if provided.
pub fn plan_uninstall(meta: &PackageMetadata, rootfs: &str) -> Vec<PlanStep> {
    let name = &meta.identity.name;
    let mut steps = Vec::new();

    // Ensure the directory exists
    steps.push(PlanStep {
        op: StepOp::Mkdir,
        command: format!("{}/var/lib/cogman/uninstallers", rootfs),
        workdir: rootfs.to_string(),
        env: Vec::new(),
        fail_policy: FailPolicy::Warn,
    });

    // Write a shell script that contains the [uninstaller] steps
    if let Some(ref uninstaller) = meta.uninstaller {
        for cmd in &uninstaller.steps {
            steps.push(PlanStep {
                op: StepOp::Exec,
                command: cmd.clone(),
                workdir: rootfs.to_string(),
                env: Vec::new(),
                fail_policy: FailPolicy::Warn,
            });
        }
    }

    steps
}
