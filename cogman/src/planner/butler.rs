/*
 * cogman/src/planner/butler.rs - Tactical Planner HUD
 *
 * The "Butler" logging personality for Cogman.
 * Covers the full Linux build/package/service ecosystem with a
 * composed British butler voice — polite under pressure, quietly
 * scathing when the operator does something ill-advised.
 *
 * Honorific selection:
 *   "sir"             — default, routine operations
 *   "your grace"      — smooth, elegant outcomes (cache hits, clean validation)
 *   "your highness"   — major milestones (large dep-graphs resolved, big installs)
 *   "my lord"         — grave / critical failures
 *   "your excellency" — security and policy matters
 *   "good master"     — friendly, instructional guidance
 */

use std::fmt::Display;
use std::time::{SystemTime, UNIX_EPOCH};

const CLR_HUD:  &str = "\x1b[96m";
const CLR_SYS:  &str = "\x1b[97m";
const CLR_DIM:  &str = "\x1b[90m";
const CLR_OK:   &str = "\x1b[92m";
const CLR_WARN: &str = "\x1b[93m";
const CLR_FAIL: &str = "\x1b[91m";
const CLR_GOLD: &str = "\x1b[33m";
const BOLD:     &str = "\x1b[1m";
const RESET:    &str = "\x1b[0m";

fn ts() -> String {
    let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default();
    let s   = now.as_secs() % 86400;
    format!("{}[{:02}:{:02}:{:02}]{}", CLR_DIM, s / 3600, (s % 3600) / 60, s % 60, RESET)
}

fn pfx(label: &str, color: &str) -> String {
    format!("{} {}{}{}▐ {} ▌{}", ts(), BOLD, color, RESET, label, RESET)
}

// ── Opening & Closing ─────────────────────────────────────────────────────

/// Display the opening salutation banner.
pub fn greet() {
    eprintln!();
    eprintln!("{}{}  ╔══════════════════════════════════════════════════╗{}", BOLD, CLR_HUD, RESET);
    eprintln!("{}{}  ║         ▐ C O G M A N ▌  Build Steward          ║{}", BOLD, CLR_HUD, RESET);
    eprintln!("{}{}  ║    Your faithful systems butler, at your service. ║{}", CLR_HUD, CLR_DIM, RESET);
    eprintln!("{}{}  ╚══════════════════════════════════════════════════╝{}", BOLD, CLR_HUD, RESET);
    eprintln!();
}

/// Shutdown / completion banner.
pub fn farewell() {
    eprintln!();
    eprintln!("{}{}  ▐ COGMAN ▌  Duties discharged. Good day, sir.{}", CLR_DIM, CLR_DIM, RESET);
    eprintln!();
}

// ── Routine Operations ────────────────────────────────────────────────────

/// Routine informational message — delivered with measured composure.
/// Honorific: "sir"
pub fn info<T: Display>(msg: T) {
    eprintln!("{} {}If I may, sir — {}{}", pfx("PLAN", CLR_HUD), CLR_SYS, msg, RESET);
}

/// A subordinate build step is being executed.
/// Honorific: "sir"
pub fn step<T: Display>(msg: T) {
    eprintln!("{} {}{}  ▶  {}{}", pfx("EXEC", CLR_DIM), CLR_DIM, BOLD, msg, RESET);
}

/// An inspection or validation is in progress.
/// Honorific: "sir"
pub fn check<T: Display>(msg: T) {
    eprintln!("{} {}Pray allow me to verify, sir — {}{}", pfx(" CHK", CLR_HUD), CLR_SYS, msg, RESET);
}

// ── Success Tiers ─────────────────────────────────────────────────────────

/// Standard success — composed satisfaction.
/// Honorific: "sir"
pub fn success<T: Display>(msg: T) {
    eprintln!("{} {}Very good, sir. {}{}", pfx(" OK ", CLR_OK), CLR_SYS, msg, RESET);
}

/// Smooth, elegant outcome — no friction whatsoever.
/// Honorific: "your grace"
pub fn smooth<T: Display>(msg: T) {
    eprintln!("{} {}Quite effortlessly done, your grace. {}{}", pfx(" OK ", CLR_OK), CLR_SYS, msg, RESET);
}

/// Major milestone — worthy of elevated address.
/// Honorific: "your highness"
pub fn milestone<T: Display>(msg: T) {
    eprintln!("{} {}{}Magnificent, your highness! {}{}", pfx("████", CLR_GOLD), BOLD, CLR_GOLD, msg, RESET);
}

// ── Warnings & Advice ─────────────────────────────────────────────────────

/// Advisory note — offered with tactful discretion.
/// Honorific: "sir"
pub fn advise<T: Display>(advice: T) {
    eprintln!("{} {}A word of counsel, if I may, sir: {}{}", pfx("ADVS", CLR_WARN), CLR_WARN, advice, RESET);
}

/// General warning — concern noted without alarm.
/// Honorific: "sir"
pub fn warn<T: Display>(msg: T) {
    eprintln!("{} {}I feel I ought to mention, sir — {}{}", pfx("WARN", CLR_WARN), CLR_WARN, msg, RESET);
}

/// Cache was hit — labour spared through prior diligence.
/// Honorific: "your grace"
pub fn cache_hit<T: Display>(msg: T) {
    eprintln!("{} {}I took the liberty of consulting my records, your grace. {}{}", pfx("CACH", CLR_OK), CLR_SYS, msg, RESET);
}

// ── Errors ────────────────────────────────────────────────────────────────

/// A recoverable error has occurred.
/// Honorific: "sir"
pub fn error<T: Display>(msg: T) {
    eprintln!("{} {}I'm afraid there's been a spot of bother, sir: {}{}", pfx("FAIL", CLR_FAIL), CLR_FAIL, msg, RESET);
}

/// A critical, unrecoverable failure — delivered with grave composure.
/// Honorific: "my lord"
pub fn fatal<T: Display>(msg: T) {
    eprintln!("{} {}{}My lord, I must report a most grave situation:{} {}{}{}", pfx("CRIT", CLR_FAIL), BOLD, CLR_FAIL, RESET, CLR_FAIL, msg, RESET);
}

/// A security or policy boundary has been crossed.
/// Honorific: "your excellency"
pub fn policy_deny<T: Display>(msg: T) {
    eprintln!("{} {}{}I must firmly decline, your excellency.{} Policy forbids it: {}{}{}", pfx("SECY", CLR_FAIL), BOLD, CLR_FAIL, RESET, CLR_FAIL, msg, RESET);
    eprintln!("{} {}{}If you believe this to be in error, review the policy stanza in your package definition.{}", pfx("    ", CLR_DIM), CLR_DIM, CLR_DIM, RESET);
}

// ── User Blunders (the best part) ─────────────────────────────────────────

/// The operator has done something questionable.
/// Honorific: suppressed exasperation + "sir"
pub fn blunder<T: Display>(msg: T) {
    eprintln!("{} {}{}Forgive me for saying so, sir, but...{} {}{}{}", pfx("AHEM", CLR_WARN), BOLD, CLR_WARN, RESET, CLR_WARN, msg, RESET);
}

/// Operator bypassed the cache deliberately.
pub fn no_cache_taunt() {
    blunder("you have instructed me to ignore the perfectly serviceable cache I spent considerable effort constructing. Very well, sir. I shall rebuild from scratch, as you apparently prefer.");
}

/// Operator is keeping temporary build directories.
pub fn keep_tmp_taunt() {
    blunder("you've asked me to leave the temporary directories in place. The estate will look rather cluttered. I shan't say another word about it, sir.");
}

/// Operator tried to install a package that's already installed.
pub fn already_installed(name: &str) {
    blunder(&format!(
        "'{}' is already very much in residence, sir. \
         One wonders what prompted a second installation. \
         Perhaps a 'cogman pkg upgrade' was the intended order?",
        name
    ));
}

/// Operator tried to remove a package that isn't installed.
pub fn not_installed(name: &str) {
    blunder(&format!(
        "'{}' does not appear to be installed, sir. \
         One cannot evict a tenant who never took up residence. \
         Might I suggest 'cogman pkg list' to survey what is actually present?",
        name
    ));
}

/// Operator tried to start a service that's already running.
pub fn already_running(name: &str) {
    blunder(&format!(
        "'{}' is already running quite contentedly, sir. \
         Starting it again would accomplish very little. \
         If you intended a restart, 'cogman svc restart {}' is the order you seek.",
        name, name
    ));
}

/// Operator tried to stop a service that isn't running.
pub fn already_stopped(name: &str) {
    blunder(&format!(
        "'{}' is not currently running, sir. \
         Stopping something that has already stopped is, with respect, \
         a somewhat futile endeavour.",
        name
    ));
}

/// Operator referenced a service that doesn't exist.
pub fn unknown_service(name: &str) {
    error(&format!(
        "'{}' is not on my roster, sir. \
         It either hasn't been loaded or the name is misspelled. \
         Might I suggest consulting '/etc/cogman/services' for the correct designation?",
        name
    ));
}

/// Operator issued a completely unrecognised command.
pub fn unknown_command(verb: &str) {
    blunder(&format!(
        "'{}' is not a recognised order, sir. \
         I've served many masters, and not one of them has ever issued that instruction. \
         Perhaps 'cogman --help' would prove illuminating?",
        verb
    ));
}

/// Circular dependency detected — grave and slightly incredulous.
pub fn circular_dep(cycle: &str) {
    fatal(&format!(
        "The packages have formed a circular dependency, my lord: {}. \
         They appear to be waiting for one another indefinitely — \
         a predicament that no amount of patience on my part can resolve.",
        cycle
    ));
}

/// A required binary (planner/executor) could not be located.
pub fn binary_missing(name: &str) {
    fatal(&format!(
        "I have searched high and low for '{}', my lord, and cannot find it. \
         Please ensure the binary is installed and present on PATH, \
         or place it alongside the cogman executable.",
        name
    ));
}

/// Network access is required but policy forbids it.
pub fn network_denied(pkg: &str) {
    policy_deny(&format!(
        "Package '{}' requires network access to build, \
         yet the policy stanza explicitly forbids it. \
         This contradiction cannot be resolved by wishing, your excellency — \
         either permit network access in the policy, or provide the sources locally.",
        pkg
    ));
}

/// A build step has failed mid-execution.
pub fn step_failed(step: &str, exit_code: i32) {
    fatal(&format!(
        "Build step '{}' has failed with exit code {}, my lord. \
         The build cannot continue in good conscience. \
         Inspect the output above for the root cause.",
        step, exit_code
    ));
}

/// Metadata file is malformed or unreadable.
pub fn bad_metadata(path: &str, reason: &str) {
    fatal(&format!(
        "The package definition at '{}' is, I'm sorry to say, rather confused, my lord. \
         Reason: {}. \
         Might I suggest a careful proof-read of the TOML? \
         The schema documentation is at docs/planner/metadata.md.",
        path, reason
    ));
}

/// Validation errors in metadata — user wrote bad config.
pub fn validation_failed(errors: &str) {
    blunder(&format!(
        "the package definition has not passed validation, sir. \
         With respect, this suggests the definition was authored in haste. \
         Errors found: {}",
        errors
    ));
}

/// Dependency could not be resolved (missing package).
pub fn dep_missing(pkg: &str, dep: &str) {
    fatal(&format!(
        "Package '{}' declares a dependency on '{}', my lord, \
         but I cannot locate it anywhere in the metadata tree. \
         Either add the dependency's TOML definition, \
         or remove it from the 'depends' list if it was listed in error.",
        pkg, dep
    ));
}

/// Filesystem permission error during build/install.
pub fn permission_denied(path: &str) {
    fatal(&format!(
        "Permission has been denied for '{}', my lord. \
         The operating system is rather firm on this point. \
         Verify that the process has adequate privileges, \
         or that Landlock policy has not been configured too restrictively.",
        path
    ));
}

/// Disk space is critically low.
pub fn low_disk(path: &str, available_mb: u64) {
    fatal(&format!(
        "I'm afraid the filesystem at '{}' has only {}MB remaining, my lord. \
         This is wholly insufficient for the proposed operation. \
         Please attend to the storage situation before proceeding.",
        path, available_mb
    ));
}

/// A package version conflict was detected.
pub fn version_conflict(pkg: &str, required: &str, found: &str) {
    warn(&format!(
        "Package '{}' requires version '{}', sir, \
         but the installed version is '{}'. \
         This may cause instability. \
         An upgrade is advisable before we proceed.",
        pkg, required, found
    ));
}

/// The AI advisor is being consulted (offline/no backend available).
pub fn advisor_unavailable() {
    warn(
        "I would normally consult the AI advisor on this matter, sir, \
         but no inference backend appears to be available. \
         Neither Ollama nor the local GGUF model responded. \
         You shall have to rely on my unaided counsel, \
         which I trust is sufficient."
    );
}

/// Rootfs target is non-standard — worth noting.
pub fn nonstandard_rootfs(rootfs: &str) {
    warn(&format!(
        "The rootfs target is '{}', sir, which is not the system root. \
         I shall install there as instructed, but do ensure \
         this is deliberate and not a typographical mishap.",
        rootfs
    ));
}

/// Plan was written to an output file successfully.
pub fn plan_written(path: &str, steps: usize) {
    milestone(&format!(
        "The execution plan has been committed to '{}' — {} step(s) standing ready. \
         The build may now proceed at your convenience, your highness.",
        path, steps
    ));
}

/// Dependency graph resolved — size-dependent honorific.
pub fn deps_resolved(count: usize) {
    if count == 1 {
        success("Dependency graph resolved. A solitary package stands ready, sir.");
    } else if count <= 10 {
        success(format!("Build order resolved — {} packages in the queue, sir.", count));
    } else {
        milestone(format!(
            "Build order resolved — {} packages marshalled and ready to march, your highness. \
             A formidable undertaking.",
            count
        ));
    }
}
