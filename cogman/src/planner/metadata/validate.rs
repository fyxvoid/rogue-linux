/*
 * cogman/src/planner/metadata/validate.rs - Semantic Metadata Validator
 *
 * This file performs deep semantic validation on package metadata, 
 * checking for logical errors that go beyond basic structural typing.
 *
 * Why: To catch configuration errors during the planning phase, 
 * preventing build failures in the subsequent execution loop.
 */

use crate::metadata::schema::{PackageMetadata, SourceKind, BuildSystem, BuildVariant};
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

    // Source file required only when kind is tarball or git
    match meta.identity.source.kind {
        SourceKind::Tarball | SourceKind::Git => {
            if meta.identity.source.file.as_deref().map(|f| f.is_empty()).unwrap_or(true) {
                errors.push("identity.source.file must not be empty for tarball/git sources".into());
            }
        }
        SourceKind::None | SourceKind::Local => {}
    }

    // Builder steps required unless source is none/local, system is custom, or variant is binary
    let skip_build_steps = matches!(meta.identity.source.kind, SourceKind::None | SourceKind::Local)
        || matches!(meta.build.system, BuildSystem::Custom)
        || matches!(meta.build.variant, BuildVariant::Binary);
    if !skip_build_steps && meta.build.steps.is_empty() {
        errors.push("builder.steps.commands must not be empty".into());
    }

    // Installer steps: optional for binary variant (binary.rs generates the steps)
    let skip_installer_steps = matches!(meta.build.variant, BuildVariant::Binary)
        || matches!(meta.identity.source.kind, SourceKind::None | SourceKind::Local)
        || matches!(meta.build.system, BuildSystem::Custom);
    if !skip_installer_steps && meta.installer.steps.is_empty() {
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
