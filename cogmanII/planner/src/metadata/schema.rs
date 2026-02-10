// cogmanII planner — metadata/schema.rs
// This module exists because the typed shape of valid metadata is the
// single source of truth for what a package definition looks like.
// serde derives handle structural validation automatically — if it
// deserializes, the shapes are correct.

use serde::Deserialize;

/// Top-level package metadata (single .toml file).
#[allow(dead_code)]
#[derive(Debug, Deserialize)]
pub struct PackageMetadata {
    pub identity: Identity,
    pub builder: Builder,
    pub installer: Installer,
    pub policy: Policy,
}

#[allow(dead_code)]
#[derive(Debug, Deserialize)]
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
#[derive(Debug, Deserialize)]
pub struct Source {
    pub kind: SourceKind,
    pub file: String,
}

#[derive(Debug, Deserialize, Clone, Copy, PartialEq)]
#[serde(rename_all = "lowercase")]
pub enum SourceKind {
    Tarball,
    Git,
}

#[allow(dead_code)]
#[derive(Debug, Deserialize, Default)]
pub struct Depends {
    #[serde(default)]
    pub build: Vec<String>,
    #[serde(default)]
    pub runtime: Vec<String>,
}

#[derive(Debug, Deserialize, Clone, Copy, PartialEq)]
#[serde(rename_all = "lowercase")]
pub enum BuildSystem {
    Autotools,
    Cmake,
    Meson,
    Make,
    Go,
    Rust,
    Python,
}

#[allow(dead_code)]
#[derive(Debug, Deserialize)]
pub struct Builder {
    pub system: BuildSystem,
    #[serde(default)]
    pub configure: Configure,
    pub steps: BuilderSteps,
}

#[allow(dead_code)]
#[derive(Debug, Deserialize, Default)]
pub struct Configure {
    #[serde(default)]
    pub flags: Vec<String>,
}

#[derive(Debug, Deserialize)]
pub struct BuilderSteps {
    pub commands: Vec<String>,
}

#[derive(Debug, Deserialize)]
pub struct Installer {
    pub steps: Vec<String>,
    #[serde(default)]
    pub verify: Option<Verify>,
}

#[derive(Debug, Deserialize)]
pub struct Verify {
    #[serde(default)]
    pub expected_files: Vec<String>,
    pub checksum: Option<String>,
}

#[allow(dead_code)]
#[derive(Debug, Deserialize)]
pub struct Policy {
    #[serde(default)]
    pub filesystem: Filesystem,
    #[serde(default)]
    pub network: Network,
    #[serde(default)]
    pub capabilities: Vec<String>,
}

#[allow(dead_code)]
#[derive(Debug, Deserialize)]
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
#[derive(Debug, Deserialize)]
pub struct Network {
    #[serde(default)]
    pub outbound: bool,
}

impl Default for Network {
    fn default() -> Self {
        Self { outbound: false }
    }
}
