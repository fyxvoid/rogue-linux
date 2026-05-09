/*
 * cogman/src/planner/main.rs - Build Planning Entry Point
 *
 * This file serves as the main command-line interface for the
 * Cogman Planner, orchestrating metadata loading and plan emission.
 *
 * Why: To provide a safe, user-facing gateway to the high-level
 * dependency resolution and scheduling logic.
 */
//
// Execution order:
//   parse args → load metadata → validate → resolve deps →
//   select variant → emit plan → (optional: AI on failure)

mod cli;
mod error;
mod metadata;
mod graph;
mod variants;
mod plan;
mod policy;
mod tmp;
mod butler;

#[cfg(feature = "ai")]
use cogman_advisor as ai;

use clap::Parser;
use std::path::PathBuf;
use std::process;

use cli::{Cli, Command};
use plan::Variant;

fn die(msg: &str) -> ! {
    butler::fatal(msg);
    process::exit(1);
}

// ── Planner pipeline ───────────────────────────────────────────────

/// Main entry point for the planner pipeline.
/// 
/// This function coordinates the loading, validation, and resolution of metadata,
/// and finally emits a binary execution plan.
fn run_plan(
    metadata_path_raw: PathBuf,
    variant: Variant,
    native_opt: bool,
    keep_tmp: bool,
    output: Option<PathBuf>,
    rootfs: &str,
    explain: bool,
    no_cache: bool,
) {
    let metadata_path = match std::fs::canonicalize(&metadata_path_raw) {
        Ok(p) => p,
        Err(e) => die(&format!("Cannot access metadata path {}: {}", metadata_path_raw.display(), e)),
    };

    butler::greet();

    // Notify if rootfs target is non-standard
    if rootfs != "/" {
        butler::nonstandard_rootfs(rootfs);
    }

    // Step 0: Cache key — computed after loading meta; checked before emitting.
    // We load metadata first so the key reflects actual content.
    // Step 1: Load TOML metadata
    butler::info(format!("Loading package definition: {}", metadata_path.display()));
    let meta = match metadata::load_metadata(&metadata_path) {
        Ok(m) => m,
        Err(e) => {
            #[cfg(feature = "ai")]
            if explain {
                let advisor = ai::create_advisor();
                if advisor.is_available() {
                    butler::info("Consulting the AI advisor on this metadata mishap, sir. One moment...");
                } else {
                    butler::advisor_unavailable();
                }
            }
            #[cfg(not(feature = "ai"))]
            let _ = explain;
            butler::bad_metadata(&metadata_path.display().to_string(), &e.to_string());
            process::exit(1);
        }
    };

    // Step 2: Semantic validation
    butler::check(format!("Validating package schema for '{}'", meta.identity.name));
    if let Err(e) = metadata::validate(&meta) {
        #[cfg(feature = "ai")]
        if explain {
            let advisor = ai::create_advisor();
            let ctx = ai::context::AiContext::new(meta.clone()).with_error(e.to_string());
            if let Some(advice) = advisor.explain_failure(&ctx) {
                butler::advise(advice);
            }
        }
        butler::validation_failed(&e.to_string());
        die("Validation error(s) found — the build cannot proceed in good conscience");
    }
    butler::smooth(format!("'{}' passed schema validation without a single complaint.", meta.identity.name));

    // Step 3: Resolve dependency graph
    butler::info("Resolving the dependency graph — tracing the full lineage of requirements...");

    let metadata_root = metadata_path
        .parent() // name dir
        .and_then(|p| p.parent()) // group dir
        .and_then(|p| p.parent()) // packages dir
        .and_then(|p| p.parent()) // workspace root
        .map(|p| p.to_path_buf())
        .unwrap_or_else(|| {
            butler::warn("Could not infer metadata root from input path — falling back to current directory");
            std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."))
        });

    let mut loader = graph::resolve::RecursiveLoader::new(metadata_root.clone());
    if let Err(e) = loader.inject_root(&meta) {
        #[cfg(feature = "ai")]
        if explain {
            let advisor = ai::create_advisor();
            let ctx = ai::context::AiContext::new(meta.clone()).with_error(e.to_string());
            if let Some(advice) = advisor.explain_failure(&ctx) {
                butler::advise(advice);
            }
        }
        die(&format!("Dependency loading failed: {}", e));
    }

    let build_list = match graph::topo::resolve_order(&loader.graph) {
        Ok(order) => order.order,
        Err(e) => {
            #[cfg(feature = "ai")]
            if explain {
                let advisor = ai::create_advisor();
                let ctx = ai::context::AiContext::new(meta.clone()).with_error(e.to_string());
                if let Some(advice) = advisor.explain_failure(&ctx) {
                    butler::advise(advice);
                }
            }
            // Check if it sounds like a cycle
            let msg = e.to_string();
            if msg.to_lowercase().contains("cycle") || msg.to_lowercase().contains("circular") {
                butler::circular_dep(&msg);
            }
            die(&format!("Dependency resolution failed: {}", msg))
        }
    };

    butler::deps_resolved(build_list.len());

    // Step 4: Policy enforcement — check each resolved package
    butler::check("Enforcing package policies — security boundaries are not optional");
    for pkg_name in &build_list {
        let pkg_meta = match loader.metadata.get(pkg_name) {
            Some(m) => m,
            None => die(&format!("Internal inconsistency, my lord — metadata missing for resolved package '{}'", pkg_name)),
        };
        if let Err(e) = policy::enforce_write_target(&pkg_meta.policy, rootfs) {
            butler::policy_deny(&format!("[{}] {}", pkg_name, e));
            process::exit(1);
        }
        let all_steps: Vec<String> = pkg_meta.build.steps.iter()
            .chain(pkg_meta.installer.steps.iter())
            .cloned()
            .collect();
        if let Err(e) = policy::enforce_network(&pkg_meta.policy, policy::steps_require_network(&all_steps)) {
            butler::network_denied(pkg_name);
            let _ = e; // message already delivered
            process::exit(1);
        }
    }
    butler::success(format!(
        "All {} package{} cleared policy inspection, your excellency. The estate is secure.",
        build_list.len(),
        if build_list.len() == 1 { "" } else { "s" }
    ));

    butler::info(format!("Assembling the execution plan for {} package(s)...", build_list.len()));

    let mut all_steps = Vec::new();

    for pkg_name in &build_list {
        let pkg_meta = match loader.metadata.get(pkg_name) {
            Some(m) => m,
            None => die(&format!("Metadata missing for resolved package: {}", pkg_name)),
        };
        butler::step(format!("Planning steps for '{}'", pkg_name));
        let mut pkg_steps = variants::plan_variant(pkg_meta, rootfs, variant, native_opt, &metadata_root);
        all_steps.append(&mut pkg_steps);
    }

    if keep_tmp {
        all_steps.retain(|s| s.op != plan::StepOp::Cleanup);
        butler::keep_tmp_taunt();
    }

    // Step 5: Cache check
    let cache_key = format!(
        "{}_v{}_r{:x}_kt{}",
        plan::cache::compute_cache_key(&meta),
        variant as u32,
        plan::cache::fnv1a_str(rootfs),
        keep_tmp as u8,
    );

    butler::info(format!("Plan assembled — {} step(s) ready for emission.", all_steps.len()));

    match output {
        Some(ref path) => {
            if !no_cache {
                if let Some(cached_bytes) = plan::cache::load(&cache_key) {
                    match std::fs::write(path, &cached_bytes) {
                        Ok(_) => {
                            butler::cache_hit(format!(
                                "An identical plan was on file. Served from cache → {}",
                                path.display()
                            ));
                            butler::farewell();
                            return;
                        }
                        Err(e) => {
                            butler::advise(format!(
                                "I attempted to serve from cache, but the write to '{}' failed ({}). \
                                 I shall plan fresh — do forgive the delay.",
                                path.display(), e
                            ));
                        }
                    }
                }
            } else {
                plan::cache::invalidate(&cache_key);
                butler::no_cache_taunt();
            }

            // Cache miss or bypass: emit fresh plan.
            let mut buf: Vec<u8> = Vec::new();
            if let Err(e) = plan::emit_plan(&all_steps, variant, &mut buf) {
                die(&format!("Failed to serialise the execution plan: {}", e));
            }
            if let Err(e) = std::fs::write(path, &buf) {
                // Check for permission issues
                if e.kind() == std::io::ErrorKind::PermissionDenied {
                    butler::permission_denied(&path.display().to_string());
                }
                die(&format!("Cannot write plan file {}: {}", path.display(), e));
            }
            if let Err(e) = plan::cache::save(&cache_key, &buf) {
                butler::advise(format!(
                    "The plan was written successfully, but I could not file a copy in the cache: {}. \
                     Future runs will need to re-plan. A minor inconvenience, sir.",
                    e
                ));
            }
            butler::plan_written(&path.display().to_string(), all_steps.len());
            butler::farewell();
        }
        None => {
            // stdout output — no caching (non-deterministic consumer).
            let mut stdout = std::io::stdout().lock();
            if let Err(e) = plan::emit_plan(&all_steps, variant, &mut stdout) {
                die(&format!("Failed to write plan to standard output: {}", e));
            }
            butler::success("The plan has been emitted to standard output, sir. Receiving process may proceed.");
            butler::farewell();
        }
    }
}

fn run_uninstall(metadata_path_raw: PathBuf, output: Option<PathBuf>, rootfs: &str) {
    let metadata_path = match std::fs::canonicalize(&metadata_path_raw) {
        Ok(p) => p,
        Err(e) => die(&format!("Cannot access metadata path {}: {}", metadata_path_raw.display(), e)),
    };

    butler::info(format!("Loading package definition for uninstall: {}", metadata_path.display()));
    let meta = match metadata::load_metadata(&metadata_path) {
        Ok(m) => m,
        Err(e) => {
            butler::bad_metadata(&metadata_path.display().to_string(), &e.to_string());
            process::exit(1);
        }
    };

    if meta.uninstaller.is_none() || meta.uninstaller.as_ref().map(|u| u.steps.is_empty()).unwrap_or(true) {
        butler::warn(format!("Package '{}' has no [uninstaller] stanza — nothing to do", meta.identity.name));
        process::exit(0);
    }

    let steps = variants::binary::plan_uninstall(&meta, rootfs);

    butler::info(format!("Uninstall plan: {} step(s) for '{}'", steps.len(), meta.identity.name));

    match output {
        Some(ref path) => {
            let mut buf: Vec<u8> = Vec::new();
            if let Err(e) = plan::emit_plan(&steps, plan::Variant::Binary, &mut buf) {
                die(&format!("Failed to serialise uninstall plan: {}", e));
            }
            if let Err(e) = std::fs::write(path, &buf) {
                die(&format!("Cannot write plan file {}: {}", path.display(), e));
            }
            butler::plan_written(&path.display().to_string(), steps.len());
        }
        None => {
            let mut stdout = std::io::stdout().lock();
            if let Err(e) = plan::emit_plan(&steps, plan::Variant::Binary, &mut stdout) {
                die(&format!("Failed to write uninstall plan to stdout: {}", e));
            }
        }
    }
    butler::farewell();
}

fn main() {
    let cli = Cli::parse();

    match cli.command {
        Command::Build {
            metadata,
            binary: _,
            build_native,
            native,
            keep_tmp,
            output,
            rootfs,
            explain,
            no_cache,
        } => {
            let variant = if build_native { Variant::Native } else { Variant::Binary };
            run_plan(metadata, variant, native, keep_tmp, output, &rootfs, explain, no_cache);
        }

        Command::Install {
            metadata,
            output,
            rootfs,
        } => {
            run_plan(metadata, Variant::Binary, false, false, output, &rootfs, false, false);
        }

        Command::Uninstall { metadata, output, rootfs } => {
            run_uninstall(metadata, output, &rootfs);
        }

        Command::Deploy {
            metadata,
            binary: _,
            build_native,
            native,
            keep_tmp,
            output,
            rootfs,
            explain,
            no_cache,
        } => {
            let variant = if build_native { Variant::Native } else { Variant::Binary };
            run_plan(metadata, variant, native, keep_tmp, output, &rootfs, explain, no_cache);
        }
    }
}
