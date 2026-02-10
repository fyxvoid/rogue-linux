// cogmanII planner — cli/mod.rs
// This module exists because CLI concerns (arg parsing, flag validation)
// should not pollute the planner's decision logic. main.rs dispatches
// to this module, which returns a validated configuration struct.

pub mod args;

pub use args::{Cli, Command};
