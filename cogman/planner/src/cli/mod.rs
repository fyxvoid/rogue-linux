// cogmanII planner — cli/mod.rs
// CLI module entry point.
// should not pollute the planner's decision logic. main.rs dispatches
// to this module, which returns a validated configuration struct.

pub mod args;

pub use args::{Cli, Command};
