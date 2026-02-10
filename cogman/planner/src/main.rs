// cogman planner — main.rs
// This is the CLI entry point. It does exactly three things:
//   1. Parse command-line arguments (cli/)
//   2. Dispatch to the planner pipeline (run_plan)
//   3. Exit with the right code
//
// It does NOT contain business logic, validation, or plan emission.
// Those responsibilities live in their own modules.
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
mod tmp;
mod ai;

use clap::Parser;
use std::path::PathBuf;
use std::process;

use cli::{Cli, Command};
use plan::Variant;

// ── Logging ────────────────────────────────────────────────────────
// Cogman butler personality. Kept in main.rs because these are
// presentation-layer concerns, not planner logic.

fn log_info(msg: &str) {
    eprintln!("\x1b[94m\x1b[1m▐ COGMAN II ▌\x1b[0m \x1b[97m{}, sir.\x1b[0m", msg);
}

fn log_ok(msg: &str) {
    eprintln!(
        "\x1b[94m\x1b[1m▐ COGMAN II ▌\x1b[0m \x1b[92m{}. Quite satisfactory, sir.\x1b[0m",
        msg
    );
}

fn log_err(msg: &str) {
    eprintln!(
        "\x1b[94m\x1b[1m▐ COGMAN II ▌\x1b[0m \x1b[91m{}. Deeply unfortunate, sir.\x1b[0m",
        msg
    );
}

fn die(msg: &str) -> ! {
    log_err(msg);
    process::exit(1);
}

// ── Planner pipeline ───────────────────────────────────────────────

fn run_plan(
    metadata_path: PathBuf,
    variant: Variant,
    native_opt: bool,
    keep_tmp: bool,
    output: Option<PathBuf>,
    rootfs: &str,
    explain: bool,
) {
    // Step 1: Load TOML metadata
    log_info(&format!("Parsing metadata from {}", metadata_path.display()));
    let meta = match metadata::load_metadata(&metadata_path) {
        Ok(m) => m,
        Err(e) => {
            if explain {
                let advisor = ai::create_advisor();
                if advisor.is_available() {
                    log_info("Consulting AI advisor about metadata failure...");
                    // No package context yet, just the error
                    // We'll skip for now or provide a dummy context
                }
            }
            die(&format!("Metadata parse failure: {}", e))
        }
    };

    // Step 2: Semantic validation
    log_info("Conducting thorough metadata inspection");
    if let Err(e) = metadata::validate(&meta) {
        if explain {
            let advisor = ai::create_advisor();
            let ctx = ai::context::AiContext::new(meta.clone()).with_error(e.to_string());
            if let Some(advice) = advisor.explain_failure(&ctx) {
                log_info("AI Advisor's Analysis:");
                eprintln!("\x1b[93m{}\x1b[0m", advice);
            }
        }
        log_err(&format!("Validation failed:\n{}", e));
        die("Validation error(s) found");
    }
    log_ok("Metadata validation passed");

    // Step 3: Resolve dependency graph
    log_info("Resolving dependency graph (recursive)");
    
    let metadata_dir = metadata_path
        .parent()
        .and_then(|p| p.parent())
        .and_then(|p| p.parent())
        .map(|p| p.to_path_buf())
        .unwrap_or_else(|| {
            log_err("Could not infer metadata root from input path");
            PathBuf::from(".")
        });
        
    let mut loader = graph::resolve::RecursiveLoader::new(metadata_dir);
    if let Err(e) = loader.inject_root(&meta) {
        if explain {
            let advisor = ai::create_advisor();
            let ctx = ai::context::AiContext::new(meta.clone()).with_error(e.to_string());
            if let Some(advice) = advisor.explain_failure(&ctx) {
                log_info("AI Advisor's Analysis:");
                eprintln!("\x1b[93m{}\x1b[0m", advice);
            }
        }
        die(&format!("Dependency loading failed: {}", e));
    }

    // ... rest of the pipeline ...
    let build_list = match graph::topo::resolve_order(&loader.graph) {
        Ok(order) => order.order,
        Err(e) => {
            if explain {
                let advisor = ai::create_advisor();
                let ctx = ai::context::AiContext::new(meta.clone()).with_error(e.to_string());
                if let Some(advice) = advisor.explain_failure(&ctx) {
                    log_info("AI Advisor's Analysis:");
                    eprintln!("\x1b[93m{}\x1b[0m", advice);
                }
            }
            die(&format!("Dependency resolution failed: {}", e))
        }
    };
    
    log_info(&format!(
        "Build order resolved: {} package(s)",
        build_list.len()
    ));

    log_info(&format!(
        "Planning install for {} package(s)", build_list.len()
    ));

    let mut all_steps = Vec::new();

    for pkg_name in &build_list {
        let pkg_meta = match loader.metadata.get(pkg_name) {
            Some(m) => m,
            None => die(&format!("Metadata missing for resolved package: {}", pkg_name)),
        };

        let mut pkg_steps = variants::plan_variant(pkg_meta, rootfs, variant, native_opt);
        all_steps.append(&mut pkg_steps);
    }
    
    if keep_tmp {
        all_steps.retain(|s| s.op != plan::StepOp::Cleanup);
        log_info("Temporary directories will be preserved (--keep-tmp)");
    }

    log_info(&format!("Emitting plan with {} step(s)", all_steps.len()));
    match output {
        Some(ref path) => {
            let mut file = match std::fs::File::create(path) {
                Ok(f) => f,
                Err(e) => die(&format!(
                    "Cannot create plan file {}: {}", path.display(), e
                )),
            };
            if let Err(e) = plan::emit_plan(&all_steps, variant, &mut file) {
                die(&format!("Failed to write plan: {}", e));
            }
            log_ok(&format!("Plan written to {}", path.display()));
        }
        None => {
            let mut stdout = std::io::stdout().lock();
            if let Err(e) = plan::emit_plan(&all_steps, variant, &mut stdout) {
                die(&format!("Failed to write plan: {}", e));
            }
            log_ok("Plan written to stdout");
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
        } => {
            let variant = if build_native { Variant::Native } else { Variant::Binary };
            run_plan(metadata, variant, native, keep_tmp, output, &rootfs, explain);
        }

        Command::Install {
            metadata,
            output,
            rootfs,
        } => {
            run_plan(metadata, Variant::Binary, false, false, output, &rootfs, false);
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
        } => {
            let variant = if build_native { Variant::Native } else { Variant::Binary };
            run_plan(metadata, variant, native, keep_tmp, output, &rootfs, explain);
        }
    }
}
