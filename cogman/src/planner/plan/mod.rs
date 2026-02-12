/*
 * cogman/src/planner/plan/mod.rs - Execution Plan Engine
 *
 * This module coordinates the translation of metadata into binary 
 * execution plans and manages the shared layout definitions.
 *
 * Why: To bridge the gap between high-level package definitions and 
 * low-level execution instructions.
 */
//
// The C executor's plan.h must match layout.rs exactly.

pub mod layout;
pub mod emit;

pub use layout::{Variant, StepOp, FailPolicy, PlanStep};
pub use emit::emit_plan;
