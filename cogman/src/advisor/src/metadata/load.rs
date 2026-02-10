// cogman planner — metadata/load.rs
// Metadata file I/O.
// deserialization and validation. If the TOML library changes,
// only this file needs to change.

use std::path::Path;
use crate::metadata::schema::PackageMetadata;

pub fn load_metadata(path: &Path) -> Result<PackageMetadata, anyhow::Error> {
    let content = std::fs::read_to_string(path)?;
    let meta: PackageMetadata = toml::from_str(&content)?;
    Ok(meta)
}
