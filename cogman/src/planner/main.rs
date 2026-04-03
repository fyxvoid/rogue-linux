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
    butler::error(msg);
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

    // Step 0: Cache key — computed after loading meta; checked before emitting.
    // We load metadata first so the key reflects actual content.
    // Step 1: Load TOML metadata
    butler::info(format!("Loading metadata: {}", metadata_path.display()));
    let meta = match metadata::load_metadata(&metadata_path) {
        Ok(m) => m,
        Err(e) => {
            #[cfg(feature = "ai")]
            if explain {
                let advisor = ai::create_advisor();
                if advisor.is_available() {
                    butler::info("Consulting AI advisor about this metadata failure...");
                }
            }
            #[cfg(not(feature = "ai"))]
            let _ = explain;
            die(&format!("Metadata parse failure: {}", e))
        }
    };

    // Step 2: Semantic validation
    butler::check("Validating package schema");
    if let Err(e) = metadata::validate(&meta) {
        #[cfg(feature = "ai")]
        if explain {
            let advisor = ai::create_advisor();
            let ctx = ai::context::AiContext::new(meta.clone()).with_error(e.to_string());
            if let Some(advice) = advisor.explain_failure(&ctx) {
                butler::advise(advice);
            }
        }
        butler::error(format!("Validation failed:\n{}", e));
        die("Validation error(s) found");
    }
    butler::success("Validation passed");

    // Step 3: Resolve dependency graph
    butler::info("Resolving dependency graph");
    
    let metadata_root = metadata_path
        .parent() // name dir
        .and_then(|p| p.parent()) // group dir
        .and_then(|p| p.parent()) // packages dir
        .and_then(|p| p.parent()) // workspace root
        .map(|p| p.to_path_buf())
        .unwrap_or_else(|| {
            butler::error("Could not infer metadata root from input path");
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

    // ... rest of the pipeline ...
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
            die(&format!("Dependency resolution failed: {}", e))
        }
    };
    
    butler::success(format!("Build order resolved ({} packages)", build_list.len()));

    // Step 4: Policy enforcement — check each resolved package
    butler::check("Enforcing package policies");
    for pkg_name in &build_list {
        let pkg_meta = match loader.metadata.get(pkg_name) {
            Some(m) => m,
            None => die(&format!("Metadata missing for policy check: {}", pkg_name)),
        };
        if let Err(e) = policy::enforce_write_target(&pkg_meta.policy, rootfs) {
            die(&format!("[{}] Policy violation: {}", pkg_name, e));
        }
        let all_steps: Vec<String> = pkg_meta.build.steps.iter()
            .chain(pkg_meta.installer.steps.iter())
            .cloned()
            .collect();
        if let Err(e) = policy::enforce_network(&pkg_meta.policy, policy::steps_require_network(&all_steps)) {
            die(&format!("[{}] Policy violation: {}", pkg_name, e));
        }
    }
    butler::success("All package policies satisfied");

    butler::info(format!("Planning installation for {} packages", build_list.len()));

    let mut all_steps = Vec::new();

    for pkg_name in &build_list {
        let pkg_meta = match loader.metadata.get(pkg_name) {
            Some(m) => m,
            None => die(&format!("Metadata missing for resolved package: {}", pkg_name)),
        };

        let mut pkg_steps = variants::plan_variant(pkg_meta, rootfs, variant, native_opt, &metadata_root);
        all_steps.append(&mut pkg_steps);
    }
    
    if keep_tmp {
        all_steps.retain(|s| s.op != plan::StepOp::Cleanup);
        butler::info("Temporary directories will be preserved (--keep-tmp), as you requested");
    }

    // Step 5: Cache check — skip emit if an identical plan is already cached.
    // Key encodes metadata content + variant + rootfs so that the same package
    // planned for different targets or build modes gets distinct cache entries.
    let cache_key = format!(
        "{}_v{}_r{:x}_kt{}",
        plan::cache::compute_cache_key(&meta),
        variant as u32,
        plan::cache::fnv1a_str(rootfs),
        keep_tmp as u8,
    );

    butler::info(format!("Emitting plan ({} steps)", all_steps.len()));
    match output {
        Some(ref path) => {
            // Cache hit: copy cached bytes directly to the output path.
            if !no_cache {
                if let Some(cached_bytes) = plan::cache::load(&cache_key) {
                    match std::fs::write(path, &cached_bytes) {
                        Ok(_) => {
                            butler::success(format!(
                                "Plan served from cache [{}.plan] → {}",
                                cache_key, path.display()
                            ));
                            return;
                        }
                        Err(e) => {
                            butler::advise(format!(
                                "Cache write failed ({}), re-planning", e
                            ));
                        }
                    }
                }
            } else {
                plan::cache::invalidate(&cache_key);
                butler::info("Cache bypassed (--no-cache)");
            }

            // Cache miss or bypass: emit fresh plan.
            let mut buf: Vec<u8> = Vec::new();
            if let Err(e) = plan::emit_plan(&all_steps, variant, &mut buf) {
                die(&format!("Failed to serialize plan: {}", e));
            }
            if let Err(e) = std::fs::write(path, &buf) {
                die(&format!("Cannot write plan file {}: {}", path.display(), e));
            }
            // Persist to cache for next run.
            if let Err(e) = plan::cache::save(&cache_key, &buf) {
                butler::advise(format!("Could not save plan to cache: {}", e));
            }
            butler::success(format!("Plan written to {}", path.display()));
        }
        None => {
            // stdout output — no caching (non-deterministic consumer).
            let mut stdout = std::io::stdout().lock();
            if let Err(e) = plan::emit_plan(&all_steps, variant, &mut stdout) {
                die(&format!("Failed to write plan: {}", e));
            }
            butler::success("Plan emitted to stdout");
        }
    }
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
