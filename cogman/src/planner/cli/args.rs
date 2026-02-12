/*
 * cogman/src/planner/cli/args.rs - CLI Argument Definitions
 *
 * This file defines the Clap-based argument schema and semantic 
 * validation rules for Cogman's user-facing flags.
 *
 * Why: To enforce a rigorous and user-friendly interface for 
 * configuring build and deployment runs.
 */

use clap::{Parser, Subcommand};
use std::path::PathBuf;

#[derive(Parser)]
#[command(
    name = "cogman",
    about = "Cogman build planner — TOML metadata to binary execution plan",
    version
)]
pub struct Cli {
    #[command(subcommand)]
    pub command: Command,
}

#[derive(Subcommand)]
pub enum Command {
    /// Plan a package build
    Build {
        /// Path to package .toml metadata
        metadata: PathBuf,

        /// Force binary install variant (prebuilt, no compilation)
        #[arg(long, conflicts_with = "build_native")]
        binary: bool,

        /// Force native build variant (compile on this machine)
        #[arg(long = "build", id = "build_native")]
        build_native: bool,

        /// Enable CPU-native optimizations (requires --build)
        #[arg(long, requires = "build_native")]
        native: bool,

        /// Do not delete temporary build directories
        #[arg(long)]
        keep_tmp: bool,

        /// Output plan file path (default: stdout)
        #[arg(short, long)]
        output: Option<PathBuf>,

        /// Target rootfs directory
        #[arg(long, default_value = "/mnt/rogue")]
        rootfs: String,

        /// Explain failures using local AI
        #[arg(long)]
        explain: bool,
    },

    /// Plan a package install (alias for build --binary)
    Install {
        /// Path to package .toml metadata
        metadata: PathBuf,

        /// Output plan file path
        #[arg(short, long)]
        output: Option<PathBuf>,

        /// Target rootfs directory
        #[arg(long, default_value = "/mnt/rogue")]
        rootfs: String,
    },

    /// Plan a full deployment
    Deploy {
        /// Path to package .toml metadata
        metadata: PathBuf,

        /// Force binary install variant
        #[arg(long, conflicts_with = "build_native")]
        binary: bool,

        /// Force native build variant
        #[arg(long = "build", id = "build_native")]
        build_native: bool,

        /// Enable CPU-native optimizations
        #[arg(long, requires = "build_native")]
        native: bool,

        /// Do not delete temporary build directories
        #[arg(long)]
        keep_tmp: bool,

        /// Output plan file path
        #[arg(short, long)]
        output: Option<PathBuf>,

        /// Target rootfs directory
        #[arg(long, default_value = "/mnt/rogue")]
        rootfs: String,

        /// Explain failures using local AI
        #[arg(long)]
        explain: bool,
    },
}
