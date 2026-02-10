// cogmanII planner — plan/layout.rs
// This module exists because the binary plan format is a contract
// between the Rust planner and the C executor. These constants and
// repr(C, packed) structs MUST match executor/plan/plan.h exactly.
// Any change here requires a matching change in the C header.

/// Plan file magic: "CGM2PLAN"
pub const PLAN_MAGIC: [u8; 8] = *b"CGM2PLAN";
pub const PLAN_VERSION: u32 = 1;
pub const HEADER_SIZE: usize = 64;
pub const STEP_SIZE: usize = 128;

/// Install variant encoded in the plan header.
#[derive(Debug, Clone, Copy, PartialEq)]
#[repr(u32)]
pub enum Variant {
    Binary = 0,
    Native = 1,
}

/// Step operation codes — one per syscall domain.
#[derive(Debug, Clone, Copy, PartialEq)]
#[repr(u32)]
pub enum StepOp {
    Exec    = 0,
    Mkdir   = 1,
    Copy    = 2,
    Verify  = 3,
    Cleanup = 4,
}

/// Per-step failure policy.
#[derive(Debug, Clone, Copy, PartialEq)]
#[repr(u32)]
pub enum FailPolicy {
    Abort = 0,
    Warn  = 1,
}

/// A single execution step (high-level, before serialization).
#[derive(Debug, Clone)]
pub struct PlanStep {
    pub op: StepOp,
    pub command: String,
    pub workdir: String,
    pub env: Vec<(String, String)>,
    pub fail_policy: FailPolicy,
}

/// Binary plan header — 64 bytes, packed.
/// Written by emit.rs, read by C executor via mmap.
#[repr(C, packed)]
pub(crate) struct PlanHeader {
    pub magic: [u8; 8],
    pub version: u32,
    pub variant: u32,
    pub step_count: u32,
    pub strtab_offset: u32,
    pub _reserved: [u8; 40],
}

/// Binary step record — 128 bytes, packed.
/// All offsets point into the string table.
#[repr(C, packed)]
pub(crate) struct StepRecord {
    pub op: u32,
    pub fail_policy: u32,
    pub cmd_offset: u32,
    pub cmd_len: u32,
    pub wdir_offset: u32,
    pub wdir_len: u32,
    pub env_offset: u32,
    pub env_len: u32,
    pub _reserved: [u8; 96],
}
