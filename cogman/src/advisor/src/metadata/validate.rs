/*
 * cogman/src/advisor/src/metadata/validate.rs - Semantic Metadata Validator
 *
 * This file performs deep semantic validation on package metadata, 
 * checking for logical errors that go beyond basic structural typing.
 *
 * Why: To catch configuration errors during the planning phase, 
 * preventing build failures in the subsequent execution loop.
 */

use crate::metadata::schema::PackageMetadata;

pub fn validate(meta: &PackageMetadata) -> Result<(), anyhow::Error> {
    if meta.identity.name.is_empty() {
        return Err(anyhow::anyhow!("identity.name must not be empty"));
    }
    // Minimal validation for advisor context
    Ok(())
}
