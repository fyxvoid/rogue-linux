// cogmanII planner — variants/native.rs
// This module exists because native builds have a fundamentally
// different lifecycle from binary installs: they need temporary
// directories, environment injection, and a verification gate
// between build and install.

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
) -> Vec<PlanStep> {
    let name = &meta.identity.name;
    let pkgroot = format!("{}/pkgroot/{}", rootfs, name);
    let tmpdir = format!("/tmp/cogmanII-build-{}", name);

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

    // Phase 2: Builder steps (extract, configure)
    for cmd in &meta.builder.steps.commands {
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
