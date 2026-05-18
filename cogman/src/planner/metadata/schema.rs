/*
 * cogman/src/planner/metadata/schema.rs - Metadata Schema Definitions
 *
 * This file defines the Rust structures that reflect the package.toml
 * schema v1.0, including identity, dependencies, and build instructions.
 *
 * Why: To maintain a strict type contract that governs all package
 * definitions in the Rogue Linux ecosystem.
 */

use std::collections::HashMap;
use serde::{Deserialize, Serialize};

/// Top-level package metadata (single .toml file).
/// This structure mirrors the `package.toml` schema version 1.0.
#[allow(dead_code)]
#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct PackageMetadata {
    /// Basic identification (name, version, etc)
    pub identity: Identity,
    /// Build instructions and system type
    #[allow(missing_docs)]
    pub build: Builder,
    /// Post-build installation steps
    pub installer: Installer,
    /// Optional steps to reverse the installation
    #[serde(default)]
    pub uninstaller: Option<Uninstaller>,
    /// Security and system policies
    #[serde(default)]
    pub policy: Policy,
    /// SHA-256 checksums to verify after installation: filename → sha256hex.
    /// Each entry will be emitted as a VERIFY step with the sha256:<hash>:<path> format.
    #[serde(default)]
    pub checksums: Option<HashMap<String, String>>,
    /// Packages that must already be installed before this plan can run.
    /// The planner checks /var/lib/cogman/installed.db and aborts if any are missing.
    #[serde(default)]
    pub build_deps: Option<Vec<String>>,
}

#[allow(dead_code)]
#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct Identity {
    pub name: String,
    pub version: String,
    pub category: String,
    pub summary: String,
    pub source: Source,
    #[serde(default)]
    pub depends: Depends,
}

#[allow(dead_code)]
#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct Source {
    pub kind: SourceKind,
    #[serde(default)]
    pub file: Option<String>,
}

#[derive(Debug, Deserialize, Serialize, Clone, Copy, PartialEq)]
#[serde(rename_all = "lowercase")]
pub enum SourceKind {
    Tarball,
    Git,
    None,
    Local,
}

#[allow(dead_code)]
#[derive(Debug, Deserialize, Serialize, Default, Clone)]
pub struct Depends {
    #[serde(default)]
    pub build: Vec<String>,
    #[serde(default)]
    pub runtime: Vec<String>,
}

#[derive(Debug, Deserialize, Serialize, Clone, Copy, PartialEq)]
#[serde(rename_all = "lowercase")]
pub enum BuildSystem {
    Autotools,
    Cmake,
    Meson,
    Make,
    Go,
    Rust,
    Python,
    Custom,
}

#[derive(Debug, Deserialize, Serialize, Clone, Copy, PartialEq, Default)]
#[serde(rename_all = "lowercase")]
pub enum BuildVariant {
    #[default]
    Binary,
    Native,
}

#[allow(dead_code)]
#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct Builder {
    pub system: BuildSystem,
    #[serde(default)]
    pub configure: Configure,
    pub steps: Vec<String>,
    /// Override the CLI-level variant for this package.
    /// "native" forces source compilation; "binary" (default) expects a prebuilt archive.
    #[serde(default)]
    pub variant: BuildVariant,
}

#[allow(dead_code)]
#[derive(Debug, Deserialize, Serialize, Default, Clone)]
pub struct Configure {
    #[serde(default)]
    pub flags: Vec<String>,
}

// BuilderSteps struct removed

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct Installer {
    pub steps: Vec<String>,
    #[serde(default)]
    pub verify: Option<Verify>,
    /// Files this package installs, relative to rootfs (e.g. "/usr/bin/nmap").
    /// Written to /var/lib/cogman/manifests/<name>.manifest on install;
    /// used by the auto-generated uninstall path to remove exactly these files.
    #[serde(default)]
    pub manifest: Vec<String>,
}

#[derive(Debug, Deserialize, Serialize, Clone, Default)]
pub struct Uninstaller {
    #[serde(default)]
    pub steps: Vec<String>,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct Verify {
    #[serde(default)]
    pub expected_files: Vec<String>,
    pub checksum: Option<String>,
}

#[derive(Debug, Deserialize, Serialize, Default, Clone)]
pub struct Policy {
    #[serde(default)]
    pub filesystem: Filesystem,
    #[serde(default)]
    pub network: Network,
    #[serde(default)]
    pub capabilities: Vec<String>,
}

#[allow(dead_code)]
#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct Filesystem {
    #[serde(default = "default_read")]
    pub read: Vec<String>,
    #[serde(default = "default_write")]
    pub write: Vec<String>,
}

impl Default for Filesystem {
    fn default() -> Self {
        Self {
            read: default_read(),
            write: default_write(),
        }
    }
}

fn default_read() -> Vec<String> {
    vec!["/".to_string()]
}

fn default_write() -> Vec<String> {
    vec!["/usr".to_string()]
}

#[allow(dead_code)]
#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct Network {
    #[serde(default)]
    pub outbound: bool,
}

impl Default for Network {
    fn default() -> Self {
        Self { outbound: false }
    }
}
