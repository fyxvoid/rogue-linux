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

    // Emit SHA-256 checksum verify steps declared in [checksums].
    // Format understood by verify_step() in verify.c: sha256:<64hexhash>:<filepath>
    if let Some(ref checksums) = meta.checksums {
        let mut sorted: Vec<(&String, &String)> = checksums.iter().collect();
        sorted.sort_by_key(|(k, _)| k.as_str());
        for (path, hash) in sorted {
            steps.push(PlanStep {
                op: StepOp::Verify,
                command: format!("sha256:{}:{}", hash, path),
                workdir: rootfs.to_string(),
                env: Vec::new(),
                fail_policy: FailPolicy::Abort,
            });
        }
    }

    // Emit a manifest-write step for any declared [installer.manifest] files.
    // Writes /var/lib/cogman/manifests/<name>.manifest so uninstall can clean up
    // without relying solely on the author-provided [uninstaller] stanza.
    if !meta.installer.manifest.is_empty() {
        let manifest_dir  = format!("{}/var/lib/cogman/manifests", rootfs);
        let manifest_path = format!("{}/{}.manifest", manifest_dir, name);
        steps.push(PlanStep {
            op: StepOp::Mkdir,
            command: manifest_dir,
            workdir: rootfs.to_string(),
            env: Vec::new(),
            fail_policy: FailPolicy::Warn,
        });
        let file_list = meta.installer.manifest
            .iter()
            .map(|f| f.as_str())
            .collect::<Vec<_>>()
            .join("\n");
        steps.push(PlanStep {
            op: StepOp::Exec,
            command: format!("printf '%s\\n' {} > {}", file_list, manifest_path),
            workdir: rootfs.to_string(),
            env: Vec::new(),
            fail_policy: FailPolicy::Warn,
        });
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

    // Run explicit [uninstaller] steps first (author-defined removal).
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

    // Auto-remove files declared in [installer.manifest] that weren't
    // already covered by the [uninstaller] stanza.
    if !meta.installer.manifest.is_empty() {
        let manifest_path = format!("{}/var/lib/cogman/manifests/{}.manifest", rootfs, name);
        // Remove every file listed in the manifest (one per line).
        steps.push(PlanStep {
            op: StepOp::Exec,
            command: format!(
                "[ -f {mp} ] && xargs -a {mp} -I{{}} rm -f -- {{}} ; rm -f {mp}",
                mp = manifest_path
            ),
            workdir: rootfs.to_string(),
            env: Vec::new(),
            fail_policy: FailPolicy::Warn,
        });
    }

    steps
}
