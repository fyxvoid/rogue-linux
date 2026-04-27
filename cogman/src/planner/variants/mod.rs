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

use crate::metadata::{PackageMetadata, BuildVariant};
use crate::plan::layout::{PlanStep, Variant};

/// Select the appropriate variant planner.
/// The package toml can override the CLI-level variant via `[build].variant`.
pub fn plan_variant(
    meta: &PackageMetadata,
    rootfs: &str,
    variant: Variant,
    native_opt: bool,
    metadata_root: &std::path::Path,
) -> Vec<PlanStep> {
    let effective = match meta.build.variant {
        BuildVariant::Native => Variant::Native,
        BuildVariant::Binary => variant, // fall through to CLI default
    };
    match effective {
        Variant::Binary => binary::plan(meta, rootfs, metadata_root),
        Variant::Native => native::plan(meta, rootfs, native_opt, metadata_root),
    }
}
