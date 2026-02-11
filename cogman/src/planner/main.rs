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
mod butler;

#[cfg(feature = "ai")]
use cogman_advisor as ai;

#[cfg(not(feature = "ai"))]
mod ai {
    use std::path::PathBuf;
    pub struct AiContext { pub package: crate::metadata::PackageMetadata }
    impl AiContext { 
        pub fn new(pkg: crate::metadata::PackageMetadata) -> Self { Self { package: pkg } }
        pub fn with_error(self, _err: String) -> Self { self }
    }
    pub trait AiAdvisor {
        fn explain_failure(&self, _ctx: &AiContext) -> Option<String> { None }
        fn is_available(&self) -> bool { false }
    }
    pub struct NoopAdvisor;
    impl AiAdvisor for NoopAdvisor {}
    pub fn create_advisor() -> Box<dyn AiAdvisor> { Box::new(NoopAdvisor) }
}

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
    butler::info(format!("Loading metadata: {}", metadata_path.display()));
    let meta = match metadata::load_metadata(&metadata_path) {
        Ok(m) => m,
        Err(e) => {
            if explain {
                let advisor = ai::create_advisor();
                if advisor.is_available() {
                    butler::info("Consulting AI advisor about this metadata failure...");
                }
            }
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
    
    let metadata_dir = metadata_path
        .parent()
        .and_then(|p| p.parent())
        .and_then(|p| p.parent())
        .map(|p| p.to_path_buf())
        .unwrap_or_else(|| {
            butler::error("Could not infer metadata root from input path");
            PathBuf::from(".")
        });
        
    let mut loader = graph::resolve::RecursiveLoader::new(metadata_dir);
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

    butler::info(format!("Planning installation for {} packages", build_list.len()));

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
        butler::info("Temporary directories will be preserved (--keep-tmp), as you requested");
    }

    butler::info(format!("Emitting plan ({} steps)", all_steps.len()));
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
            butler::success(format!("Plan written to {}", path.display()));
        }
        None => {
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
