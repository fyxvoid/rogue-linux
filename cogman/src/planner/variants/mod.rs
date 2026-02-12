/*
 * cogman/src/planner/variants/mod.rs - Build Strategy Variants
 *
 * This module provides the abstractions for different build and 
 * installation strategies (e.g., Native compilation vs. Binary deployment).
 *
 * Why: To allow Cogman to support diverse build lifecycles within 
 * a unified planning interface.
 */

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
    metadata_root: &std::path::Path,
) -> Vec<PlanStep> {
    match variant {
        Variant::Binary => binary::plan(meta, rootfs, metadata_root),
        Variant::Native => native::plan(meta, rootfs, native_opt, metadata_root),
    }
}
