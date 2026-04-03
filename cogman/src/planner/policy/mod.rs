/*
 * cogman/src/planner/policy/mod.rs - Build Policy Enforcement
 *
 * This module validates that planning operations respect the constraints
 * declared in each package's [policy] section before any steps are emitted.
 *
 * Why: Policy is only useful if it is checked. Enforcing at plan-time
 * catches violations before the executor touches the filesystem.
 */

use crate::metadata::schema::Policy;
use crate::error::PlannerError;

/// Validate that the rootfs target path sits within at least one
/// allowed write path declared by the package policy.
///
/// A write path of "/" permits any destination (the default).
pub fn enforce_write_target(policy: &Policy, rootfs: &str) -> Result<(), PlannerError> {
    if policy.filesystem.write.is_empty() {
        return Err(PlannerError::PolicyViolation(
            "policy.filesystem.write is empty — no write destination is permitted".into(),
        ));
    }

    let allowed = policy.filesystem.write.iter().any(|allowed_path| {
        allowed_path == "/"
            || rootfs == allowed_path
            || rootfs.starts_with(&format!("{}/", allowed_path))
    });

    if !allowed {
        return Err(PlannerError::PolicyViolation(format!(
            "rootfs target '{}' is not within any allowed write path {:?}",
            rootfs, policy.filesystem.write
        )));
    }

    Ok(())
}

/// Validate that the package does not require outbound network access
/// when the policy forbids it.
///
/// `has_download_steps` should be true when the build steps include
/// commands that fetch from the network (curl, wget, git clone, etc.).
pub fn enforce_network(policy: &Policy, has_download_steps: bool) -> Result<(), PlannerError> {
    if !policy.network.outbound && has_download_steps {
        return Err(PlannerError::PolicyViolation(
            "package policy forbids outbound network access, \
             but build steps appear to require it (curl/wget/git clone detected)"
                .into(),
        ));
    }
    Ok(())
}

/// Heuristic: detect download commands in build/installer step strings.
pub fn steps_require_network(steps: &[String]) -> bool {
    let network_cmds = ["curl ", "wget ", "git clone", "git fetch", "pip install", "npm install", "cargo fetch"];
    steps.iter().any(|step| {
        network_cmds.iter().any(|cmd| step.contains(cmd))
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::metadata::schema::{Policy, Filesystem, Network};

    fn policy_with_write(paths: Vec<&str>) -> Policy {
        Policy {
            filesystem: Filesystem {
                read: vec!["/".into()],
                write: paths.iter().map(|s| s.to_string()).collect(),
            },
            network: Network { outbound: false },
            capabilities: vec![],
        }
    }

    #[test]
    fn test_write_target_slash_allows_any() {
        let p = policy_with_write(vec!["/"]);
        assert!(enforce_write_target(&p, "/mnt/rogue").is_ok());
        assert!(enforce_write_target(&p, "/anything").is_ok());
    }

    #[test]
    fn test_write_target_exact_match() {
        let p = policy_with_write(vec!["/mnt/rogue"]);
        assert!(enforce_write_target(&p, "/mnt/rogue").is_ok());
    }

    #[test]
    fn test_write_target_prefix_match() {
        let p = policy_with_write(vec!["/mnt"]);
        assert!(enforce_write_target(&p, "/mnt/rogue").is_ok());
    }

    #[test]
    fn test_write_target_denied() {
        let p = policy_with_write(vec!["/mnt/rogue"]);
        assert!(enforce_write_target(&p, "/tmp/bad").is_err());
    }

    #[test]
    fn test_network_blocked() {
        let p = policy_with_write(vec!["/"]);
        let result = enforce_network(&p, true);
        assert!(result.is_err());
    }

    #[test]
    fn test_network_allowed_when_no_download() {
        let p = policy_with_write(vec!["/"]);
        assert!(enforce_network(&p, false).is_ok());
    }

    #[test]
    fn test_steps_require_network_detects_curl() {
        let steps = vec!["curl -O https://example.com/file.tar.gz".to_string()];
        assert!(steps_require_network(&steps));
    }

    #[test]
    fn test_steps_require_network_clean() {
        let steps = vec!["make -j4".to_string(), "make install".to_string()];
        assert!(!steps_require_network(&steps));
    }
}
