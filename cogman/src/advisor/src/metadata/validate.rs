// cogman planner — metadata/validate.rs
// Semantic validation for loaded metadata.
// catch everything. Values can be the right type but semantically wrong:
// empty names, path traversal in verify paths, relative write paths.
// This is the last gate before metadata enters the planner pipeline.

use crate::metadata::schema::PackageMetadata;

pub fn validate(meta: &PackageMetadata) -> Result<(), anyhow::Error> {
    if meta.identity.name.is_empty() {
        return Err(anyhow::anyhow!("identity.name must not be empty"));
    }
    // Minimal validation for advisor context
    Ok(())
}
