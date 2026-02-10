// cogmanII planner — metadata/mod.rs
// This module exists because metadata handling has three distinct phases:
// 1. Load: read bytes from disk and deserialize TOML
// 2. Schema: define the typed shape of valid metadata
// 3. Validate: check semantic constraints beyond structural typing
//
// Keeping these phases in separate files makes it obvious where
// a metadata-related bug lives.

pub mod schema;
pub mod load;
pub mod validate;

pub use schema::PackageMetadata;
pub use load::load_metadata;
pub use validate::validate;
