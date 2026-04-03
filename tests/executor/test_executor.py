"""
tests/executor/test_executor.py - Executor Integration Tests

Builds synthetic binary plan files in Python and runs cogman-executor
against them to verify correct step dispatch, error handling, and
security enforcement.

The plan format is mirrored from plan.h (64-byte header, 128-byte steps,
variable string table) — no dependency on the Rust planner binary.
"""

import os
import struct
import subprocess
import tempfile
import unittest

# ── Constants (must match plan.h) ─────────────────────────────────

PLAN_MAGIC   = b"CGM2PLAN"
PLAN_VERSION = 1
HEADER_SIZE  = 64
STEP_SIZE    = 128

VARIANT_BINARY = 0
VARIANT_NATIVE = 1

OP_EXEC    = 0
OP_MKDIR   = 1
OP_COPY    = 2
OP_VERIFY  = 3
OP_CLEANUP = 4

FAIL_ABORT = 0
FAIL_WARN  = 1

ROOT     = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EXECUTOR = os.path.join(ROOT, "bin", "cogman-executor")


# ── Plan builder ──────────────────────────────────────────────────

class PlanBuilder:
    """Pure-Python binary plan writer — mirrors emit.rs logic exactly.

    Note: VARIANT_BINARY triggers supervisor/idle mode in the executor
    (designed for init-style deployment). Use VARIANT_NATIVE for unit
    tests that just need to run steps and exit.
    """

    def __init__(self, variant=VARIANT_NATIVE):
        self.variant = variant
        self.steps = []      # list of (op, fail_policy, cmd, wdir, env_pairs)
        self._strtab = bytearray()

    def _add_str(self, s: str):
        offset = len(self._strtab)
        data = s.encode("utf-8")
        self._strtab.extend(data)
        self._strtab.append(0)
        return offset, len(data)

    def _add_env(self, pairs):
        if not pairs:
            return 0, 0
        offset = len(self._strtab)
        total = 0
        for k, v in pairs:
            entry = f"{k}={v}".encode("utf-8")
            self._strtab.extend(entry)
            self._strtab.append(0)
            total += len(entry) + 1
        return offset, total

    def add_step(self, op, cmd, wdir="/", env=None, fail_policy=FAIL_ABORT):
        self.steps.append((op, fail_policy, cmd, wdir, env or []))
        return self

    def build(self) -> bytes:
        # First pass: build string table and collect step records
        step_count = len(self.steps)
        strtab_offset = HEADER_SIZE + step_count * STEP_SIZE
        records = []

        # Reset strtab
        self._strtab = bytearray()

        for (op, fail_policy, cmd, wdir, env) in self.steps:
            cmd_off,  cmd_len  = self._add_str(cmd)
            wdir_off, wdir_len = self._add_str(wdir)
            env_off,  env_len  = self._add_env(env)
            records.append((op, fail_policy, cmd_off, cmd_len, wdir_off, wdir_len, env_off, env_len))

        # Header: 8 magic + 4 version + 4 variant + 4 step_count + 4 strtab_offset + 40 reserved
        header = (
            PLAN_MAGIC
            + struct.pack("<I", PLAN_VERSION)
            + struct.pack("<I", self.variant)
            + struct.pack("<I", step_count)
            + struct.pack("<I", strtab_offset)
            + b"\x00" * 40
        )
        assert len(header) == HEADER_SIZE

        # Step records: 128 bytes each
        step_bytes = bytearray()
        for (op, fail_policy, cmd_off, cmd_len, wdir_off, wdir_len, env_off, env_len) in records:
            rec = (
                struct.pack("<I", op)
                + struct.pack("<I", fail_policy)
                + struct.pack("<I", 0)          # flags
                + struct.pack("<I", 0)          # reserved_flags
                + struct.pack("<I", cmd_off)
                + struct.pack("<I", cmd_len)
                + struct.pack("<I", wdir_off)
                + struct.pack("<I", wdir_len)
                + struct.pack("<I", env_off)
                + struct.pack("<I", env_len)
                + b"\x00" * 88                  # reserved
            )
            assert len(rec) == STEP_SIZE
            step_bytes.extend(rec)

        return header + bytes(step_bytes) + bytes(self._strtab)


def run_executor(plan_bytes: bytes) -> subprocess.CompletedProcess:
    """Write plan to a temp file and run cogman-executor against it."""
    with tempfile.NamedTemporaryFile(suffix=".plan", delete=False) as f:
        f.write(plan_bytes)
        plan_path = f.name
    try:
        return subprocess.run(
            [EXECUTOR, plan_path],
            capture_output=True, text=True
        )
    finally:
        os.unlink(plan_path)


# ── Tests ─────────────────────────────────────────────────────────

class TestExecutorBasic(unittest.TestCase):

    def setUp(self):
        if not os.path.exists(EXECUTOR):
            self.skipTest(f"cogman-executor not found at {EXECUTOR}")

    def test_no_args_exits_nonzero(self):
        result = subprocess.run([EXECUTOR], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)

    def test_missing_plan_file_exits_nonzero(self):
        result = subprocess.run([EXECUTOR, "/nonexistent.plan"],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)

    def test_garbage_file_rejected(self):
        with tempfile.NamedTemporaryFile(suffix=".plan", delete=False) as f:
            f.write(b"this is not a plan file at all")
            path = f.name
        try:
            result = subprocess.run([EXECUTOR, path], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
        finally:
            os.unlink(path)

    def test_wrong_magic_rejected(self):
        plan = PlanBuilder().add_step(OP_EXEC, "true").build()
        bad_plan = b"BADMAGIC" + plan[8:]
        result = run_executor(bad_plan)
        self.assertNotEqual(result.returncode, 0)

    def test_empty_step_list_succeeds(self):
        """VARIANT_NATIVE with zero steps should succeed and exit immediately."""
        plan = PlanBuilder(variant=VARIANT_NATIVE).build()
        result = run_executor(plan)
        self.assertEqual(result.returncode, 0)


class TestExecutorMkdir(unittest.TestCase):

    def setUp(self):
        if not os.path.exists(EXECUTOR):
            self.skipTest(f"cogman-executor not found at {EXECUTOR}")

    def test_mkdir_creates_directory(self):
        with tempfile.TemporaryDirectory() as base:
            target = os.path.join(base, "a", "b", "c")
            plan = PlanBuilder().add_step(OP_MKDIR, target).build()
            result = run_executor(plan)
            self.assertEqual(result.returncode, 0)
            self.assertTrue(os.path.isdir(target))

    def test_mkdir_idempotent(self):
        with tempfile.TemporaryDirectory() as base:
            target = os.path.join(base, "existing")
            os.makedirs(target)
            plan = PlanBuilder().add_step(OP_MKDIR, target).build()
            result = run_executor(plan)
            self.assertEqual(result.returncode, 0)


class TestExecutorExec(unittest.TestCase):

    def setUp(self):
        if not os.path.exists(EXECUTOR):
            self.skipTest(f"cogman-executor not found at {EXECUTOR}")

    def test_exec_true_succeeds(self):
        plan = PlanBuilder().add_step(OP_EXEC, "true").build()
        result = run_executor(plan)
        self.assertEqual(result.returncode, 0)

    def test_exec_false_aborts(self):
        plan = PlanBuilder().add_step(OP_EXEC, "false", fail_policy=FAIL_ABORT).build()
        result = run_executor(plan)
        self.assertNotEqual(result.returncode, 0)

    def test_exec_false_warn_continues(self):
        """FAIL_WARN: failing step should not abort subsequent steps."""
        with tempfile.TemporaryDirectory() as base:
            sentinel = os.path.join(base, "reached")
            plan = (
                PlanBuilder()
                .add_step(OP_EXEC, "false", fail_policy=FAIL_WARN)
                .add_step(OP_EXEC, f"touch {sentinel}", fail_policy=FAIL_ABORT)
                .build()
            )
            result = run_executor(plan)
            self.assertEqual(result.returncode, 0)
            self.assertTrue(os.path.exists(sentinel),
                            "Step after FAIL_WARN should have executed")

    def test_exec_with_workdir(self):
        with tempfile.TemporaryDirectory() as base:
            sentinel = os.path.join(base, "pwd_output.txt")
            plan = PlanBuilder().add_step(
                OP_EXEC, f"pwd > {sentinel}", wdir=base
            ).build()
            result = run_executor(plan)
            self.assertEqual(result.returncode, 0)
            with open(sentinel) as f:
                self.assertEqual(f.read().strip(), base)

    def test_exec_env_injection(self):
        with tempfile.TemporaryDirectory() as base:
            sentinel = os.path.join(base, "env_output.txt")
            plan = PlanBuilder().add_step(
                OP_EXEC, f"echo $COGMAN_TEST_VAR > {sentinel}",
                env=[("COGMAN_TEST_VAR", "hello_cogman")]
            ).build()
            result = run_executor(plan)
            self.assertEqual(result.returncode, 0)
            with open(sentinel) as f:
                self.assertIn("hello_cogman", f.read())


class TestExecutorVerify(unittest.TestCase):

    def setUp(self):
        if not os.path.exists(EXECUTOR):
            self.skipTest(f"cogman-executor not found at {EXECUTOR}")

    def test_verify_existing_path_succeeds(self):
        plan = PlanBuilder().add_step(OP_VERIFY, "/bin/sh").build()
        result = run_executor(plan)
        self.assertEqual(result.returncode, 0)

    def test_verify_missing_path_fails(self):
        plan = PlanBuilder().add_step(OP_VERIFY, "/nonexistent/file/cogman_test").build()
        result = run_executor(plan)
        self.assertNotEqual(result.returncode, 0)

    def test_verify_sha256_correct_hash(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("hello cogman\n")
            fpath = f.name
        try:
            # Compute actual hash
            import hashlib
            with open(fpath, "rb") as f:
                sha = hashlib.sha256(f.read()).hexdigest()
            cmd = f"sha256:{sha}:{fpath}"
            plan = PlanBuilder().add_step(OP_VERIFY, cmd).build()
            result = run_executor(plan)
            self.assertEqual(result.returncode, 0, result.stderr)
        finally:
            os.unlink(fpath)

    def test_verify_sha256_wrong_hash_fails(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("hello cogman\n")
            fpath = f.name
        try:
            bad_hash = "a" * 64
            cmd = f"sha256:{bad_hash}:{fpath}"
            plan = PlanBuilder().add_step(OP_VERIFY, cmd).build()
            result = run_executor(plan)
            self.assertNotEqual(result.returncode, 0)
        finally:
            os.unlink(fpath)


class TestExecutorCopy(unittest.TestCase):

    def setUp(self):
        if not os.path.exists(EXECUTOR):
            self.skipTest(f"cogman-executor not found at {EXECUTOR}")

    def test_copy_file_tree(self):
        with tempfile.TemporaryDirectory() as base:
            src = os.path.join(base, "src")
            dst = os.path.join(base, "dst")
            os.makedirs(src)
            with open(os.path.join(src, "file.txt"), "w") as f:
                f.write("cogman test")
            plan = PlanBuilder().add_step(OP_COPY, f"{src}|{dst}").build()
            result = run_executor(plan)
            self.assertEqual(result.returncode, 0)
            self.assertTrue(os.path.exists(os.path.join(dst, "file.txt")))

    def test_copy_path_traversal_rejected(self):
        """COPY with '..' in the destination path must be rejected."""
        plan = PlanBuilder().add_step(OP_COPY, "/tmp/safe|/tmp/../../../etc").build()
        result = run_executor(plan)
        self.assertNotEqual(result.returncode, 0,
                            "Path traversal in COPY dst must be rejected")

    def test_copy_traversal_in_src_rejected(self):
        plan = PlanBuilder().add_step(OP_COPY, "/tmp/../etc|/tmp/dst").build()
        result = run_executor(plan)
        self.assertNotEqual(result.returncode, 0,
                            "Path traversal in COPY src must be rejected")

    def test_copy_missing_separator_rejected(self):
        plan = PlanBuilder().add_step(OP_COPY, "/tmp/no-separator").build()
        result = run_executor(plan)
        self.assertNotEqual(result.returncode, 0)


class TestExecutorCleanup(unittest.TestCase):

    def setUp(self):
        if not os.path.exists(EXECUTOR):
            self.skipTest(f"cogman-executor not found at {EXECUTOR}")

    def test_cleanup_removes_directory(self):
        with tempfile.TemporaryDirectory() as base:
            target = os.path.join(base, "to_remove")
            os.makedirs(target)
            with open(os.path.join(target, "file"), "w") as f:
                f.write("x")
            plan = PlanBuilder().add_step(OP_CLEANUP, target).build()
            result = run_executor(plan)
            self.assertEqual(result.returncode, 0)
            self.assertFalse(os.path.exists(target))

    def test_cleanup_missing_dir_is_ok(self):
        """Cleaning up a non-existent path should not abort."""
        plan = PlanBuilder().add_step(OP_CLEANUP, "/tmp/cogman_nonexistent_dir_xyz").build()
        result = run_executor(plan)
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
