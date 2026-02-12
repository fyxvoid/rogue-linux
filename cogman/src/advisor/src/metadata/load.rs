/*
 * cogman/src/advisor/src/metadata/load.rs - Metadata Parser (TOML)
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

pub fn load_metadata(path: &Path) -> Result<PackageMetadata, anyhow::Error> {
    let content = std::fs::read_to_string(path)?;
    let meta: PackageMetadata = toml::from_str(&content)?;
    Ok(meta)
}
