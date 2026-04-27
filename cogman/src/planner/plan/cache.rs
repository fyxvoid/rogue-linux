/*
 * cogman/src/planner/plan/cache.rs - Plan Cache (FNV-64)
 *
 * Caches emitted binary plans to disk keyed by a hash of the package
 * metadata content. Identical metadata → identical plan → no re-emit.
 *
 * Why: Avoid re-running the full planning pipeline when nothing has
 * changed. Incremental rebuilds matter at 166+ packages.
 *
 * Cache location: $HOME/.cache/cogman/<hash>.plan
 * Bypass:         --no-cache CLI flag
 */

use std::fmt::Write as FmtWrite;
use std::fs;
use std::io;
use std::path::PathBuf;

use crate::metadata::schema::PackageMetadata;

// ── FNV-1a 64-bit hash ────────────────────────────────────────────

const FNV_OFFSET: u64 = 14695981039346656037;
const FNV_PRIME: u64 = 1099511628211;

/// Public FNV-1a helper — useful for composing cache keys in callers.
pub fn fnv1a_str(data: &str) -> u64 {
    fnv1a(data)
}

fn fnv1a(data: &str) -> u64 {
    let mut hash = FNV_OFFSET;
    for byte in data.bytes() {
        hash ^= byte as u64;
        hash = hash.wrapping_mul(FNV_PRIME);
    }
    hash
}

// ── Cache key ─────────────────────────────────────────────────────

/// Compute a deterministic cache key from package metadata.
///
/// The key covers everything that affects plan output:
///   name + version + variant-flag + build steps + installer steps
///   + verify expected_files + policy write paths
///
/// It does NOT cover the rootfs path (the same plan is valid for any
/// rootfs because the rootfs is embedded in the step strings, which
/// are part of the hash via the build/installer step templates).
///
/// In practice the step strings DO reference `rootfs` (passed in at
/// plan_variant time), so two plans with different rootfs values will
/// produce different step strings and therefore different hashes.
pub fn compute_cache_key(meta: &PackageMetadata) -> String {
    let mut buf = String::new();

    // Identity
    let _ = write!(buf, "{}@{}", meta.identity.name, meta.identity.version);
    let _ = write!(buf, "|cat:{}", meta.identity.category);
    let _ = write!(buf, "|src:{}", meta.identity.source.file.as_deref().unwrap_or(""));
    let _ = write!(buf, "|bv:{:?}", meta.build.variant);

    // Build steps (order matters)
    for (i, step) in meta.build.steps.iter().enumerate() {
        let _ = write!(buf, "|b{}:{}", i, step);
    }

    // Installer steps
    for (i, step) in meta.installer.steps.iter().enumerate() {
        let _ = write!(buf, "|i{}:{}", i, step);
    }

    // Verify expected files
    if let Some(ref v) = meta.installer.verify {
        for f in &v.expected_files {
            let _ = write!(buf, "|vf:{}", f);
        }
        if let Some(ref ck) = v.checksum {
            let _ = write!(buf, "|vc:{}", ck);
        }
    }

    // Policy write paths (changing policy should invalidate the cache)
    for p in &meta.policy.filesystem.write {
        let _ = write!(buf, "|pw:{}", p);
    }

    format!("{:016x}", fnv1a(&buf))
}

// ── Cache directory ───────────────────────────────────────────────

fn cache_dir() -> PathBuf {
    std::env::var("HOME")
        .map(PathBuf::from)
        .unwrap_or_else(|_| PathBuf::from("/tmp"))
        .join(".cache")
        .join("cogman")
}

pub fn cache_path(key: &str) -> PathBuf {
    cache_dir().join(format!("{}.plan", key))
}

// ── Public API ────────────────────────────────────────────────────

/// Try to load a previously cached plan for `key`.
/// Returns `Some(bytes)` if the cache entry exists and is readable,
/// `None` otherwise (cache miss, stale, or corrupted entry).
pub fn load(key: &str) -> Option<Vec<u8>> {
    let path = cache_path(key);
    if !path.exists() {
        return None;
    }
    fs::read(&path).ok()
}

/// Save plan bytes to the cache under `key`.
/// Creates the cache directory if it does not exist.
/// Failures are non-fatal — the plan has already been emitted.
pub fn save(key: &str, data: &[u8]) -> io::Result<()> {
    let dir = cache_dir();
    fs::create_dir_all(&dir)?;
    let path = cache_path(key);
    fs::write(path, data)
}

/// Delete a single cache entry (useful for `--no-cache` forced rebuild).
pub fn invalidate(key: &str) {
    let _ = fs::remove_file(cache_path(key));
}

/// Remove all entries from the cogman plan cache.
pub fn clear_all() -> io::Result<()> {
    let dir = cache_dir();
    if dir.exists() {
        fs::remove_dir_all(&dir)?;
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn make_meta(name: &str, version: &str) -> PackageMetadata {
        use crate::metadata::schema::*;
        PackageMetadata {
            identity: Identity {
                name: name.to_string(),
                version: version.to_string(),
                category: "base".to_string(),
                summary: "test package".to_string(),
                source: Source { kind: SourceKind::Tarball, file: format!("{}-{}.tar.xz", name, version) },
                depends: Depends::default(),
            },
            build: Builder {
                system: BuildSystem::Make,
                configure: Configure::default(),
                steps: vec!["make -j4".to_string()],
                variant: BuildVariant::default(),
            },
            installer: Installer {
                steps: vec!["make install".to_string()],
                verify: None,
            },
            policy: Policy::default(),
        }
    }

    #[test]
    fn test_same_metadata_same_key() {
        let m1 = make_meta("bash", "5.2.21");
        let m2 = make_meta("bash", "5.2.21");
        assert_eq!(compute_cache_key(&m1), compute_cache_key(&m2));
    }

    #[test]
    fn test_different_version_different_key() {
        let m1 = make_meta("bash", "5.2.21");
        let m2 = make_meta("bash", "5.2.22");
        assert_ne!(compute_cache_key(&m1), compute_cache_key(&m2));
    }

    #[test]
    fn test_different_name_different_key() {
        let m1 = make_meta("bash", "5.2.21");
        let m2 = make_meta("zsh", "5.2.21");
        assert_ne!(compute_cache_key(&m1), compute_cache_key(&m2));
    }

    #[test]
    fn test_key_is_16_hex_chars() {
        let m = make_meta("gcc", "13.2.0");
        let key = compute_cache_key(&m);
        assert_eq!(key.len(), 16);
        assert!(key.chars().all(|c| c.is_ascii_hexdigit()));
    }
}
