// cogmanII planner — plan/emit.rs
// Plan file generation logic.
// format is a distinct concern from defining the format (layout.rs).
// The string table builder and write logic live here.

use std::io::{self, Write};
use crate::plan::layout::*;

/// String table builder — accumulates null-terminated strings
/// and returns byte offsets for the step records.
struct StringTable {
    data: Vec<u8>,
}

impl StringTable {
    fn new() -> Self {
        Self { data: Vec::new() }
    }

    /// Add a string, return (offset, length).
    fn add(&mut self, s: &str) -> (u32, u32) {
        let offset = self.data.len() as u32;
        let len = s.len() as u32;
        self.data.extend_from_slice(s.as_bytes());
        self.data.push(0); // null terminator for C
        (offset, len)
    }

    /// Serialize environment pairs as "KEY=VAL\0KEY=VAL\0".
    fn add_env(&mut self, pairs: &[(String, String)]) -> (u32, u32) {
        if pairs.is_empty() {
            return (0, 0);
        }
        let offset = self.data.len() as u32;
        let mut total_len = 0usize;
        for (k, v) in pairs {
            let entry = format!("{}={}", k, v);
            self.data.extend_from_slice(entry.as_bytes());
            self.data.push(0);
            total_len += entry.len() + 1;
        }
        (offset, total_len as u32)
    }
}

/// Emit a binary plan file to the given writer.
/// Layout: [Header 64B] [Steps N×128B] [StringTable variable]
pub fn emit_plan<W: Write>(
    steps: &[PlanStep],
    variant: Variant,
    out: &mut W,
) -> io::Result<()> {
    let step_count = steps.len() as u32;
    let strtab_offset = (HEADER_SIZE + STEP_SIZE * steps.len()) as u32;

    // Build string table and step records simultaneously
    let mut strtab = StringTable::new();
    let mut records: Vec<StepRecord> = Vec::with_capacity(steps.len());

    for step in steps {
        let (cmd_off, cmd_len) = strtab.add(&step.command);
        let (wdir_off, wdir_len) = strtab.add(&step.workdir);
        let (env_off, env_len) = strtab.add_env(&step.env);

        records.push(StepRecord {
            op: step.op as u32,
            fail_policy: step.fail_policy as u32,
            cmd_offset: cmd_off,
            cmd_len,
            wdir_offset: wdir_off,
            wdir_len,
            env_offset: env_off,
            env_len,
            _reserved: [0u8; 96],
        });
    }

    // Write header
    let header = PlanHeader {
        magic: PLAN_MAGIC,
        version: PLAN_VERSION,
        variant: variant as u32,
        step_count,
        strtab_offset,
        _reserved: [0u8; 40],
    };

    // Safety: repr(C, packed) structs written as raw bytes —
    // this is the exact format the C executor expects to mmap().
    let header_bytes: &[u8] = unsafe {
        std::slice::from_raw_parts(
            &header as *const PlanHeader as *const u8,
            HEADER_SIZE,
        )
    };
    out.write_all(header_bytes)?;

    for rec in &records {
        let rec_bytes: &[u8] = unsafe {
            std::slice::from_raw_parts(
                rec as *const StepRecord as *const u8,
                STEP_SIZE,
            )
        };
        out.write_all(rec_bytes)?;
    }

    out.write_all(&strtab.data)?;
    Ok(())
}
