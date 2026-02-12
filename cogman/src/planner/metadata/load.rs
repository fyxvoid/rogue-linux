/*
 * cogman/src/planner/metadata/load.rs - Metadata Parser (TOML)
 *
 * This file implements the on-disk loading and deserialization of
 * package.toml files into typed memory structures.
 *
 * Why: To provide a robust and safe way to ingestion package data
 * into the planning pipeline.
 */
// deserialization and validation. If the TOML library changes,
// only this file needs to change.

use std::path::Path;
use crate::metadata::schema::PackageMetadata;
use crate::error::PlannerError;

/// Read and deserialize a TOML metadata file.
/// Returns a typed PackageMetadata or a descriptive error.
pub fn load_metadata(path: &Path) -> Result<PackageMetadata, PlannerError> {
    let content = std::fs::read_to_string(path)
        .map_err(|e| PlannerError::MetadataLoad(
            format!("cannot read {}: {}", path.display(), e)
        ))?;

    toml::from_str(&content)
        .map_err(|e| PlannerError::MetadataLoad(
            format!("TOML parse error in {}: {}", path.display(), e)
        ))
}
