//! Package database — binary flat-file format, no external deps.
//!
//! Layout on disk:
//!   [DbHeader 32 bytes]
//!   [PackageEntry × count]  (fixed 512 bytes each)
//!   [string heap]           (variable, referenced by offsets in entries)
//!
//! All multi-byte integers are little-endian.
//! Path: /var/lib/cogman/packages.db

use std::fs::{self, OpenOptions};
use std::io::{self, Read, Write};
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

pub const DB_PATH: &str = "/var/lib/cogman/packages.db";
pub const DB_MAGIC: u32 = 0x434F474D; // "COGM"
pub const DB_VERSION: u16 = 1;
pub const ENTRY_SIZE: usize = 512;

/// One installed package record (fixed-size on disk, strings in heap).
#[derive(Debug, Clone)]
pub struct PackageRecord {
    pub name:         String,
    pub version:      String,
    pub category:     String,
    pub install_root: String,         // e.g. /
    pub installed_at: u64,            // unix timestamp
    pub files:        Vec<String>,    // every file/dir installed
}

impl PackageRecord {
    pub fn new(name: &str, version: &str, category: &str, root: &str) -> Self {
        PackageRecord {
            name:         name.to_string(),
            version:      version.to_string(),
            category:     category.to_string(),
            install_root: root.to_string(),
            installed_at: SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .map(|d| d.as_secs())
                .unwrap_or(0),
            files: Vec::new(),
        }
    }
}

// ── On-disk structs (little-endian, packed) ───────────────────────────────

#[repr(C, packed)]
struct RawHeader {
    magic:        u32,
    version:      u16,
    _pad:         u16,
    entry_count:  u32,
    heap_offset:  u32,
    heap_len:     u32,
    _reserved:    [u8; 12],
}

#[repr(C, packed)]
struct RawEntry {
    name_off:    u32,  name_len:    u16,
    ver_off:     u32,  ver_len:     u16,
    cat_off:     u32,  cat_len:     u16,
    root_off:    u32,  root_len:    u16,
    installed_at: u64,
    // variable-length file list stored as one blob: null-separated strings
    files_off:   u32,  files_len:   u32,
    _reserved:   [u8; ENTRY_SIZE - 4-2 - 4-2 - 4-2 - 4-2 - 8 - 4-4],
}

const _: () = assert!(std::mem::size_of::<RawHeader>() == 32);
const _: () = assert!(std::mem::size_of::<RawEntry>()  == ENTRY_SIZE);

// ── PackageDb ────────────────────────────────────────────────────────────

pub struct PackageDb {
    path:    PathBuf,
    records: Vec<PackageRecord>,
}

impl PackageDb {
    /// Open or create the database at `path`.
    pub fn open<P: AsRef<Path>>(path: P) -> io::Result<Self> {
        let path = path.as_ref().to_path_buf();

        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent)?;
        }

        let records = if path.exists() {
            Self::read_all(&path)?
        } else {
            Vec::new()
        };

        Ok(PackageDb { path, records })
    }

    /// Open the default system database.
    pub fn system() -> io::Result<Self> {
        Self::open(DB_PATH)
    }

    // ── Queries ──────────────────────────────────────────────────────────

    pub fn get(&self, name: &str) -> Option<&PackageRecord> {
        self.records.iter().find(|r| r.name == name)
    }

    pub fn has(&self, name: &str) -> bool {
        self.get(name).is_some()
    }

    pub fn list(&self) -> &[PackageRecord] {
        &self.records
    }

    pub fn count(&self) -> usize {
        self.records.len()
    }

    // ── Mutations (write-through) ─────────────────────────────────────────

    /// Insert or update a record. Flushes to disk.
    pub fn upsert(&mut self, rec: PackageRecord) -> io::Result<()> {
        if let Some(existing) = self.records.iter_mut().find(|r| r.name == rec.name) {
            *existing = rec;
        } else {
            self.records.push(rec);
        }
        self.flush()
    }

    /// Remove a record by name. Returns the removed record if it existed.
    pub fn remove(&mut self, name: &str) -> io::Result<Option<PackageRecord>> {
        if let Some(pos) = self.records.iter().position(|r| r.name == name) {
            let rec = self.records.remove(pos);
            self.flush()?;
            Ok(Some(rec))
        } else {
            Ok(None)
        }
    }

    // ── Serialization ────────────────────────────────────────────────────

    fn flush(&self) -> io::Result<()> {
        let mut heap: Vec<u8> = Vec::new();
        let mut entries: Vec<RawEntry> = Vec::new();

        for r in &self.records {
            let name_off  = Self::heap_push(&mut heap, r.name.as_bytes());
            let ver_off   = Self::heap_push(&mut heap, r.version.as_bytes());
            let cat_off   = Self::heap_push(&mut heap, r.category.as_bytes());
            let root_off  = Self::heap_push(&mut heap, r.install_root.as_bytes());

            // Encode files as null-separated blob
            let files_blob: Vec<u8> = r.files.iter()
                .flat_map(|f| f.as_bytes().iter().chain(&[0u8]).copied())
                .collect();
            let files_off = Self::heap_push(&mut heap, &files_blob);

            entries.push(RawEntry {
                name_off:     name_off as u32,
                name_len:     r.name.len() as u16,
                ver_off:      ver_off  as u32,
                ver_len:      r.version.len() as u16,
                cat_off:      cat_off  as u32,
                cat_len:      r.category.len() as u16,
                root_off:     root_off as u32,
                root_len:     r.install_root.len() as u16,
                installed_at: r.installed_at,
                files_off:    files_off as u32,
                files_len:    files_blob.len() as u32,
                _reserved:    [0u8; ENTRY_SIZE - 4-2 - 4-2 - 4-2 - 4-2 - 8 - 4-4],
            });
        }

        let heap_offset = (32 + entries.len() * ENTRY_SIZE) as u32;
        let header = RawHeader {
            magic:       DB_MAGIC,
            version:     DB_VERSION,
            _pad:        0,
            entry_count: entries.len() as u32,
            heap_offset,
            heap_len:    heap.len() as u32,
            _reserved:   [0u8; 12],
        };

        let mut f = OpenOptions::new()
            .write(true).create(true).truncate(true)
            .open(&self.path)?;

        f.write_all(Self::as_bytes(&header))?;
        for e in &entries {
            f.write_all(Self::as_bytes(e))?;
        }
        f.write_all(&heap)?;
        f.flush()
    }

    fn read_all(path: &Path) -> io::Result<Vec<PackageRecord>> {
        let mut f = fs::File::open(path)?;
        let mut buf = Vec::new();
        f.read_to_end(&mut buf)?;

        if buf.len() < 32 {
            return Err(io::Error::new(io::ErrorKind::InvalidData, "db too small"));
        }

        let hdr = unsafe { &*(buf.as_ptr() as *const RawHeader) };
        if hdr.magic != DB_MAGIC {
            return Err(io::Error::new(io::ErrorKind::InvalidData, "bad db magic"));
        }

        let count     = hdr.entry_count as usize;
        let heap_off  = hdr.heap_offset as usize;
        let heap      = buf.get(heap_off..).unwrap_or(&[]);

        let mut records = Vec::with_capacity(count);
        for i in 0..count {
            let eoff = 32 + i * ENTRY_SIZE;
            if eoff + ENTRY_SIZE > buf.len() { break; }
            let e = unsafe { &*(buf[eoff..].as_ptr() as *const RawEntry) };

            let name    = Self::read_str(heap, e.name_off as usize,  e.name_len as usize);
            let version = Self::read_str(heap, e.ver_off  as usize,  e.ver_len  as usize);
            let cat     = Self::read_str(heap, e.cat_off  as usize,  e.cat_len  as usize);
            let root    = Self::read_str(heap, e.root_off as usize,  e.root_len as usize);

            let files_blob = heap.get(
                e.files_off as usize .. (e.files_off + e.files_len) as usize
            ).unwrap_or(&[]);
            let files: Vec<String> = files_blob.split(|&b| b == 0)
                .filter(|s| !s.is_empty())
                .map(|s| String::from_utf8_lossy(s).into_owned())
                .collect();

            records.push(PackageRecord {
                name, version, category: cat, install_root: root,
                installed_at: e.installed_at,
                files,
            });
        }
        Ok(records)
    }

    fn heap_push(heap: &mut Vec<u8>, data: &[u8]) -> usize {
        let off = heap.len();
        heap.extend_from_slice(data);
        off
    }

    fn read_str(heap: &[u8], off: usize, len: usize) -> String {
        heap.get(off..off+len)
            .map(|b| String::from_utf8_lossy(b).into_owned())
            .unwrap_or_default()
    }

    fn as_bytes<T: Sized>(v: &T) -> &[u8] {
        unsafe {
            std::slice::from_raw_parts(v as *const T as *const u8, std::mem::size_of::<T>())
        }
    }
}
