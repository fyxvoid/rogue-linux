/*
 * cogman/src/planner/variants/native.rs - Native Build Strategy
 *
 * This file implements the "Native" build variant, managing 
 * source compilation, out-of-tree builds, and staged installation.
 *
 * Why: To enable high-performance, local compilation of security 
 * tools within the Rogue Linux environment.
 */

use crate::metadata::PackageMetadata;
use crate::plan::layout::{PlanStep, StepOp, FailPolicy};

/// Generate execution steps for the native build variant.
/// Sequence: tmpdir → pkgroot → builder steps → installer steps →
///           verify → copy → cleanup.
///
/// If `native_opt` is true, -march=native and -mtune=native are
/// injected into CFLAGS/CXXFLAGS via the plan environment.
pub fn plan(
    meta: &PackageMetadata,
    rootfs: &str,
    native_opt: bool,
    metadata_root: &std::path::Path,
) -> Vec<PlanStep> {
    let name = &meta.identity.name;
    let cat = &meta.identity.category;
    let pkgroot = format!("{}/pkgroot/{}", rootfs, name);
    let tmpdir = format!("/tmp/cogman-build-{}-native", name);
    
    // Absolute path to the source tar directory
    let tar_dir = metadata_root.join("packages").join(cat).join(name).join("tar");
    let tar_dir_str = tar_dir.to_string_lossy();

    // Build environment — always set PKGROOT/DESTDIR
    let mut base_env: Vec<(String, String)> = vec![
        ("PKGROOT".into(), pkgroot.clone()),
        ("DESTDIR".into(), pkgroot.clone()),
    ];

    // Inject native optimization flags if requested
    if native_opt {
        base_env.push(("CFLAGS".into(), "-march=native -mtune=native -O2".into()));
        base_env.push(("CXXFLAGS".into(), "-march=native -mtune=native -O2".into()));
    }

    let env = base_env;
    let mut steps = Vec::new();

    // Phase 1: Create directories
    steps.push(PlanStep {
        op: StepOp::Mkdir,
        command: tmpdir.clone(),
        workdir: "/".to_string(),
        env: Vec::new(),
        fail_policy: FailPolicy::Abort,
    });
    steps.push(PlanStep {
        op: StepOp::Mkdir,
        command: pkgroot.clone(),
        workdir: "/".to_string(),
        env: Vec::new(),
        fail_policy: FailPolicy::Abort,
    });

    // Phase 1.5: Symlink tar directory into tmpdir for relative paths in TOML
    steps.push(PlanStep {
        op: StepOp::Exec,
        command: format!("ln -sf {} tar", tar_dir_str),
        workdir: tmpdir.clone(),
        env: Vec::new(),
        fail_policy: FailPolicy::Abort,
    });

    // Phase 2: Builder steps (extract, configure)
    for cmd in &meta.build.steps {
        steps.push(PlanStep {
            op: StepOp::Exec,
            command: cmd.clone(),
            workdir: tmpdir.clone(),
            env: env.clone(),
            fail_policy: FailPolicy::Abort,
        });
    }

    // Phase 3: Installer steps (make, make install)
    for cmd in &meta.installer.steps {
        steps.push(PlanStep {
            op: StepOp::Exec,
            command: cmd.clone(),
            workdir: tmpdir.clone(),
            env: env.clone(),
            fail_policy: FailPolicy::Abort,
        });
    }

    // Phase 4: Verification gate — must pass before install
    if let Some(ref verify) = meta.installer.verify {
        for f in &verify.expected_files {
            steps.push(PlanStep {
                op: StepOp::Verify,
                command: format!("{}/{}", pkgroot, f),
                workdir: tmpdir.clone(),
                env: Vec::new(),
                fail_policy: FailPolicy::Abort,
            });
        }
        if let Some(ref cksum) = verify.checksum {
            steps.push(PlanStep {
                op: StepOp::Verify,
                command: format!("sha256:{}:{}/{}",
                    cksum, pkgroot,
                    verify.expected_files.first().map(|s| s.as_str()).unwrap_or("")),
                workdir: tmpdir.clone(),
                env: Vec::new(),
                fail_policy: FailPolicy::Abort,
            });
        }
    }

    // Phase 5: Copy verified artifacts into rootfs
    steps.push(PlanStep {
        op: StepOp::Copy,
        command: format!("{}|{}", pkgroot, rootfs),
        workdir: "/".to_string(),
        env: Vec::new(),
        fail_policy: FailPolicy::Abort,
    });

    // Phase 5.5: SHA-256 checksum verify steps declared in [checksums].
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

    // Phase 6: Cleanup temporary directory
    steps.push(PlanStep {
        op: StepOp::Cleanup,
        command: tmpdir,
        workdir: "/".to_string(),
        env: Vec::new(),
        fail_policy: FailPolicy::Warn,
    });

    steps
}
