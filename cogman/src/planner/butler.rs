// cogman planner — butler.rs
// Handles all user-facing communication with a distinct "British Butler" personality.
// "Cogman" treats the user as "Sir" (or "Madam", though default to "Sir" for now as per prompt)
// and the machine/packages as "resources" or "subjects" to be managed with care.

use std::fmt::Display;

const BLUE: &str = "\x1b[94m";
const BOLD: &str = "\x1b[1m";
const RESET: &str = "\x1b[0m";
const WHITE: &str = "\x1b[97m";
const GREEN: &str = "\x1b[92m";
const RED: &str = "\x1b[91m";
const YELLOW: &str = "\x1b[93m";

fn prefix() -> String {
    format!("{}{}\u{2590} COGMAN \u{258c}{}", BLUE, BOLD, RESET)
}

pub fn info<T: Display>(msg: T) {
    eprintln!("{} {}{}, sir.{}", prefix(), WHITE, msg, RESET);
}

pub fn success<T: Display>(msg: T) {
    eprintln!("{} {}{}, sir. Most satisfactory.{}", prefix(), GREEN, msg, RESET);
}

pub fn error<T: Display>(msg: T) {
    eprintln!("{} {}{}, sir. I am afraid this is rather unfortunate.{}", prefix(), RED, msg, RESET);
}

pub fn check<T: Display>(msg: T) {
    eprintln!("{} {}Checking {}, sir...{}", prefix(), BLUE, msg, RESET);
}

pub fn advise<T: Display>(advice: T) {
    eprintln!("{} {}I have taken the liberty of analyzing the situation:{}", prefix(), YELLOW, RESET);
    eprintln!("{}{}{}", YELLOW, advice, RESET);
}
