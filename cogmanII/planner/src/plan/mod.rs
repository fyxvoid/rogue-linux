// cogmanII planner — plan/mod.rs
// This module exists because plan emission has two concerns:
// 1. layout.rs: the binary format definition (constants, repr(C) structs)
// 2. emit.rs: serializing steps into that format
//
// The C executor's plan.h must match layout.rs exactly.

pub mod layout;
pub mod emit;

pub use layout::{Variant, StepOp, FailPolicy, PlanStep};
pub use emit::emit_plan;
