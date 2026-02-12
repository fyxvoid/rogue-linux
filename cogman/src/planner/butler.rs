/*
 * cogman/src/planner/butler.rs - Tactical Planner HUD
 *
 * This file implements the "Butler" logging personality for the
 * build planner, using high-contrast ANSI tactical markers.
 *
 * Why: To provide the operator with real-time, aesthetically
 * precise feedback during the build planning phase.
 */

use std::fmt::Display;
use std::time::{SystemTime, UNIX_EPOCH};

const CLR_HUD: &str = "\x1b[96m";
const CLR_SYS: &str = "\x1b[97m";
const CLR_DIM: &str = "\x1b[90m";
const CLR_OK: &str = "\x1b[92m";
const CLR_WARN: &str = "\x1b[93m";
const CLR_FAIL: &str = "\x1b[91m";
const BOLD: &str = "\x1b[1m";
const RESET: &str = "\x1b[0m";

fn get_timestamp() -> String {
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default();
    let secs = now.as_secs() % 86400;
    format!("{}[{:02}:{:02}:{:02}]{}", CLR_DIM, secs / 3600, (secs % 3600) / 60, secs % 60, RESET)
}

fn pfx(label: &str, color: &str) -> String {
    format!("{} {}{}{}▐ {} ▌{}", get_timestamp(), BOLD, color, RESET, label, RESET)
}

pub fn info<T: Display>(msg: T) {
    eprintln!("{} {}{}{}", pfx("PLAN", CLR_HUD), CLR_SYS, msg, RESET);
}

pub fn success<T: Display>(msg: T) {
    eprintln!("{} {}{}{}", pfx(" OK ", CLR_OK), CLR_SYS, msg, RESET);
}

pub fn error<T: Display>(msg: T) {
    eprintln!("{} {}FAIL: {}{}", pfx("FAIL", CLR_FAIL), CLR_FAIL, msg, RESET);
}

pub fn check<T: Display>(msg: T) {
    eprintln!("{} {}CHECK: {}{}", pfx("HUD ", CLR_HUD), CLR_SYS, msg, RESET);
}

pub fn advise<T: Display>(advice: T) {
    eprintln!("{} {}ADVICE: {}{}", pfx("WARN", CLR_WARN), CLR_WARN, advice, RESET);
}
