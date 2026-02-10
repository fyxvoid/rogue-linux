// cogman planner — tmp/mod.rs
// Temporary directory management.
// (create → build → verify → install → cleanup) is a cross-cutting
// concern that both the native variant and the plan emitter need
// to understand. Centralizing it here prevents lifecycle bugs.

pub mod lifecycle;

