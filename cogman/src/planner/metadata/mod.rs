/*
 * cogman/src/planner/metadata/mod.rs - Package Metadata Management
 *
 * This module provides the core abstractions for loading, validating, 
 * and accessing package metadata (package.toml).
 *
 * Why: To ensure that the system operates on high-fidelity, schema-valid 
 * package definitions.
 */

pub mod schema;
pub mod load;
pub mod validate;

pub use schema::{PackageMetadata, BuildVariant};
pub use load::load_metadata;
pub use validate::validate;
