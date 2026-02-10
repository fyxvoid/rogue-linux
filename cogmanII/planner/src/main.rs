// cogmanII planner — main.rs
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
) {
    // Step 1: Load TOML metadata
    log_info(&format!("Parsing metadata from {}", metadata_path.display()));
    let meta = match metadata::load_metadata(&metadata_path) {
        Ok(m) => m,
        Err(e) => die(&format!("Metadata parse failure: {}", e)),
    };

    // Step 2: Semantic validation
    log_info("Conducting thorough metadata inspection");
    if let Err(e) = metadata::validate(&meta) {
        log_err(&format!("Validation failed:\n{}", e));
        die(&format!("Validation error(s) found"));
    }
    log_ok("Metadata validation passed");

    // Step 3: Resolve dependency graph
    log_info("Resolving dependency graph");
    let mut dep_graph = graph::DepGraph::new();
    let pkg_key = format!("{}/{}", meta.identity.category, meta.identity.name);
    dep_graph.add_package(&pkg_key);
    for dep in &meta.identity.depends.build {
        dep_graph.add_dep(&pkg_key, dep);
    }
    match graph::topo::resolve_order(&dep_graph) {
        Ok(order) => {
            log_info(&format!(
                "Build order resolved: {} package(s)",
                order.order.len()
            ));
        }
        Err(e) => die(&format!("Dependency resolution failed: {}", e)),
    }

    // Step 4: Generate variant-specific steps
    let variant_name = match variant {
        Variant::Binary => "binary",
        Variant::Native => {
            if native_opt { "native (optimized)" } else { "native" }
        }
    };
    log_info(&format!(
        "Planning {} install for '{}'", variant_name, meta.identity.name
    ));

    let mut steps = variants::plan_variant(&meta, rootfs, variant, native_opt);

    // If --keep-tmp, remove cleanup steps from the plan
    if keep_tmp {
        steps.retain(|s| s.op != plan::StepOp::Cleanup);
        log_info("Temporary directories will be preserved (--keep-tmp)");
    }

    // Step 5: Emit binary plan artifact
    log_info(&format!("Emitting plan with {} step(s)", steps.len()));
    match output {
        Some(ref path) => {
            let mut file = match std::fs::File::create(path) {
                Ok(f) => f,
                Err(e) => die(&format!(
                    "Cannot create plan file {}: {}", path.display(), e
                )),
            };
            if let Err(e) = plan::emit_plan(&steps, variant, &mut file) {
                die(&format!("Failed to write plan: {}", e));
            }
            log_ok(&format!("Plan written to {}", path.display()));
        }
        None => {
            let mut stdout = std::io::stdout().lock();
            if let Err(e) = plan::emit_plan(&steps, variant, &mut stdout) {
                die(&format!("Failed to write plan: {}", e));
            }
            log_ok("Plan written to stdout");
        }
    }
}

// ── CLI dispatch ───────────────────────────────────────────────────

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
        } => {
            let variant = if build_native {
                Variant::Native
            } else {
                Variant::Binary
            };
            if native && !build_native {
                die("--native requires --build flag");
            }
            run_plan(metadata, variant, native, keep_tmp, output, &rootfs);
        }

        Command::Install {
            metadata,
            output,
            rootfs,
        } => {
            run_plan(metadata, Variant::Binary, false, false, output, &rootfs);
        }

        Command::Deploy {
            metadata,
            binary: _,
            build_native,
            native,
            keep_tmp,
            output,
            rootfs,
        } => {
            let variant = if build_native {
                Variant::Native
            } else {
                Variant::Binary
            };
            run_plan(metadata, variant, native, keep_tmp, output, &rootfs);
        }
    }
}
