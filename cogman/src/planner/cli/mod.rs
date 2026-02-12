/*
 * cogman/src/planner/cli/mod.rs - Command Line Interface
 *
 * This module is the entry point for Cogman's command-line processing, 
 * abstracting argument parsing from the core planning logic.
 *
 * Why: To provide a clean, detached interface for interacting with 
 * the build system.
 */

pub mod args;

pub use args::{Cli, Command};
