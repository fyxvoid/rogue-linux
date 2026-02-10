// cogmanII planner — variants/mod.rs
// Install variants (Binary vs Native).
// produce fundamentally different execution step sequences.
// Each variant is in its own file so the step generation logic
// is obvious and self-contained.

pub mod binary;
pub mod native;

use crate::metadata::PackageMetadata;
use crate::plan::layout::{PlanStep, Variant};

/// Select the appropriate variant planner based on CLI flags.
pub fn plan_variant(
    meta: &PackageMetadata,
    rootfs: &str,
    variant: Variant,
    native_opt: bool,
) -> Vec<PlanStep> {
    match variant {
        Variant::Binary => binary::plan(meta, rootfs),
        Variant::Native => native::plan(meta, rootfs, native_opt),
    }
}
