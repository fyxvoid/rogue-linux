// cogmanII planner — metadata/validate.rs
// This module exists because structural deserialization (serde) cannot
// catch everything. Values can be the right type but semantically wrong:
// empty names, path traversal in verify paths, relative write paths.
// This is the last gate before metadata enters the planner pipeline.

use crate::metadata::schema::PackageMetadata;
use crate::error::PlannerError;

/// Semantic validation beyond what serde can enforce.
/// Collects all errors rather than failing on the first one.
pub fn validate(meta: &PackageMetadata) -> Result<(), PlannerError> {
    let mut errors: Vec<String> = Vec::new();

    // Identity: all required fields must be non-empty
    if meta.identity.name.is_empty() {
        errors.push("identity.name must not be empty".into());
    }
    if meta.identity.version.is_empty() {
        errors.push("identity.version must not be empty".into());
    }
    if meta.identity.category.is_empty() {
        errors.push("identity.category must not be empty".into());
    }
    if meta.identity.summary.is_empty() {
        errors.push("identity.summary must not be empty".into());
    }

    // Category: alphanumeric + slash + hyphen + underscore only
    for ch in meta.identity.category.chars() {
        if !ch.is_ascii_alphanumeric() && ch != '/' && ch != '-' && ch != '_' {
            errors.push(format!(
                "identity.category contains invalid character: '{}'", ch
            ));
            break;
        }
    }

    // Source file must not be empty
    if meta.identity.source.file.is_empty() {
        errors.push("identity.source.file must not be empty".into());
    }

    // Builder: at least one command
    if meta.builder.steps.commands.is_empty() {
        errors.push("builder.steps.commands must not be empty".into());
    }

    // Installer: at least one step
    if meta.installer.steps.is_empty() {
        errors.push("installer.steps must not be empty".into());
    }

    // Verify: no path traversal allowed
    if let Some(ref verify) = meta.installer.verify {
        for f in &verify.expected_files {
            if f.contains("..") {
                errors.push(format!(
                    "installer.verify.expected_files contains traversal: {}", f
                ));
            }
        }
    }

    // Policy: write paths must be absolute
    for p in &meta.policy.filesystem.write {
        if !p.starts_with('/') {
            errors.push(format!(
                "policy.filesystem.write path must be absolute: {}", p
            ));
        }
    }

    // Dependencies: no empty entries
    for dep in &meta.identity.depends.build {
        if dep.is_empty() {
            errors.push("empty build dependency".into());
        }
    }

    if errors.is_empty() {
        Ok(())
    } else {
        Err(PlannerError::Validation(errors))
    }
}
