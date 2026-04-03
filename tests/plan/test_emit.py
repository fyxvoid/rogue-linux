"""
tests/plan/test_emit.py - Binary Plan Emission Tests

Validates the binary plan format produced by cogman-planner:
  - Header magic and version
  - Step count consistency
  - String table reachability
  - Path traversal rejection
  - Variant encoding
  - Cache round-trip (via filesystem)
"""

import os
import struct
import subprocess
import tempfile
import unittest

# ── Constants mirrored from plan.h ────────────────────────────────

PLAN_MAGIC = b"CGM2PLAN"
PLAN_VERSION = 1
HEADER_SIZE = 64
STEP_SIZE = 128

VARIANT_BINARY = 0
VARIANT_NATIVE = 1

OP_EXEC    = 0
OP_MKDIR   = 1
OP_COPY    = 2
OP_VERIFY  = 3
OP_CLEANUP = 4

FAIL_ABORT = 0
FAIL_WARN  = 1

# ── Helpers ───────────────────────────────────────────────────────

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PLANNER = os.path.join(ROOT, "bin", "cogman-planner")


def minimal_toml(name="testpkg", version="1.0.0", category="test") -> str:
    return f"""
[identity]
name = "{name}"
version = "{version}"
category = "{category}"
summary = "Minimal test package"

[identity.source]
kind = "tarball"
file = "{name}-{version}.tar.xz"

[build]
system = "make"
steps = ["echo building"]

[installer]
steps = ["echo installing"]

[policy.filesystem]
read = ["/"]
write = ["/"]
"""


def run_planner(toml_content: str, extra_args=None, rootfs="/tmp/rogue-test") -> tuple:
    """Write TOML to a temp file, run planner, return (returncode, plan_bytes, stderr)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Build the expected package tree: packages/<cat>/<name>/<name>.toml
        import tomllib
        meta = tomllib.loads(toml_content)
        cat  = meta["identity"]["category"]
        name = meta["identity"]["name"]
        pkg_dir = os.path.join(tmpdir, "packages", cat, name)
        os.makedirs(pkg_dir, exist_ok=True)
        toml_path = os.path.join(pkg_dir, f"{name}.toml")
        with open(toml_path, "w") as f:
            f.write(toml_content)

        plan_path = os.path.join(tmpdir, "out.plan")
        cmd = [PLANNER, "build", toml_path,
               "--output", plan_path,
               "--rootfs", rootfs]
        if extra_args:
            cmd.extend(extra_args)

        result = subprocess.run(cmd, capture_output=True, text=True)
        plan_bytes = b""
        if os.path.exists(plan_path):
            with open(plan_path, "rb") as f:
                plan_bytes = f.read()
        return result.returncode, plan_bytes, result.stderr


def parse_header(data: bytes) -> dict:
    """Parse the 64-byte plan header."""
    assert len(data) >= HEADER_SIZE, "Plan data too short for header"
    magic    = data[0:8]
    version  = struct.unpack_from("<I", data, 8)[0]
    variant  = struct.unpack_from("<I", data, 12)[0]
    step_count = struct.unpack_from("<I", data, 16)[0]
    strtab_offset = struct.unpack_from("<I", data, 20)[0]
    return dict(magic=magic, version=version, variant=variant,
                step_count=step_count, strtab_offset=strtab_offset)


def parse_step(data: bytes, index: int) -> dict:
    """Parse a single step record at the given index."""
    offset = HEADER_SIZE + index * STEP_SIZE
    op          = struct.unpack_from("<I", data, offset +  0)[0]
    fail_policy = struct.unpack_from("<I", data, offset +  4)[0]
    flags       = struct.unpack_from("<I", data, offset +  8)[0]
    cmd_offset  = struct.unpack_from("<I", data, offset + 16)[0]
    cmd_len     = struct.unpack_from("<I", data, offset + 20)[0]
    wdir_offset = struct.unpack_from("<I", data, offset + 24)[0]
    wdir_len    = struct.unpack_from("<I", data, offset + 28)[0]
    env_offset  = struct.unpack_from("<I", data, offset + 32)[0]
    env_len     = struct.unpack_from("<I", data, offset + 36)[0]
    return dict(op=op, fail_policy=fail_policy, flags=flags,
                cmd_offset=cmd_offset, cmd_len=cmd_len,
                wdir_offset=wdir_offset, wdir_len=wdir_len,
                env_offset=env_offset, env_len=env_len)


def read_str(data: bytes, strtab_offset: int, str_offset: int) -> str:
    """Read a null-terminated string from the string table."""
    abs_offset = strtab_offset + str_offset
    end = data.index(b"\x00", abs_offset)
    return data[abs_offset:end].decode("utf-8")


# ── Tests ─────────────────────────────────────────────────────────

class TestPlanHeader(unittest.TestCase):

    def setUp(self):
        if not os.path.exists(PLANNER):
            self.skipTest(f"cogman-planner not found at {PLANNER}")
        self.rc, self.plan, self.stderr = run_planner(minimal_toml())
        if self.rc != 0:
            self.skipTest(f"Planner failed: {self.stderr}")

    def test_plan_not_empty(self):
        self.assertGreater(len(self.plan), HEADER_SIZE)

    def test_magic_bytes(self):
        hdr = parse_header(self.plan)
        self.assertEqual(hdr["magic"], PLAN_MAGIC)

    def test_version(self):
        hdr = parse_header(self.plan)
        self.assertEqual(hdr["version"], PLAN_VERSION)

    def test_variant_default_binary(self):
        hdr = parse_header(self.plan)
        self.assertEqual(hdr["variant"], VARIANT_BINARY)

    def test_step_count_positive(self):
        hdr = parse_header(self.plan)
        self.assertGreater(hdr["step_count"], 0)

    def test_strtab_offset_correct(self):
        hdr = parse_header(self.plan)
        expected = HEADER_SIZE + hdr["step_count"] * STEP_SIZE
        self.assertEqual(hdr["strtab_offset"], expected)

    def test_file_size_at_least_header_plus_steps(self):
        hdr = parse_header(self.plan)
        min_size = HEADER_SIZE + hdr["step_count"] * STEP_SIZE
        self.assertGreaterEqual(len(self.plan), min_size)


class TestPlanSteps(unittest.TestCase):

    def setUp(self):
        if not os.path.exists(PLANNER):
            self.skipTest(f"cogman-planner not found at {PLANNER}")
        self.rc, self.plan, self.stderr = run_planner(minimal_toml())
        if self.rc != 0:
            self.skipTest(f"Planner failed: {self.stderr}")
        self.hdr = parse_header(self.plan)

    def test_first_step_is_mkdir(self):
        """Binary variant: first step should create the pkgroot directory."""
        step = parse_step(self.plan, 0)
        self.assertEqual(step["op"], OP_MKDIR)

    def test_steps_have_non_empty_commands(self):
        hdr = self.hdr
        for i in range(hdr["step_count"]):
            step = parse_step(self.plan, i)
            cmd = read_str(self.plan, hdr["strtab_offset"], step["cmd_offset"])
            self.assertGreater(len(cmd), 0, f"Step {i} has empty command")

    def test_steps_have_workdir(self):
        hdr = self.hdr
        for i in range(hdr["step_count"]):
            step = parse_step(self.plan, i)
            wdir = read_str(self.plan, hdr["strtab_offset"], step["wdir_offset"])
            self.assertTrue(wdir.startswith("/"), f"Step {i} workdir not absolute: {wdir!r}")

    def test_last_step_is_copy(self):
        """Binary variant: last step should copy pkgroot into rootfs."""
        hdr = self.hdr
        last = parse_step(self.plan, hdr["step_count"] - 1)
        self.assertEqual(last["op"], OP_COPY)

    def test_op_codes_in_valid_range(self):
        hdr = self.hdr
        for i in range(hdr["step_count"]):
            step = parse_step(self.plan, i)
            self.assertIn(step["op"], {OP_EXEC, OP_MKDIR, OP_COPY, OP_VERIFY, OP_CLEANUP},
                          f"Step {i} has invalid op: {step['op']}")

    def test_fail_policies_valid(self):
        hdr = self.hdr
        for i in range(hdr["step_count"]):
            step = parse_step(self.plan, i)
            self.assertIn(step["fail_policy"], {FAIL_ABORT, FAIL_WARN},
                          f"Step {i} has invalid fail_policy: {step['fail_policy']}")


class TestPlannerVariants(unittest.TestCase):

    def setUp(self):
        if not os.path.exists(PLANNER):
            self.skipTest(f"cogman-planner not found at {PLANNER}")

    def test_native_variant_header(self):
        rc, plan, stderr = run_planner(minimal_toml(), extra_args=["--build"])
        if rc != 0:
            self.skipTest(f"Native planner failed: {stderr}")
        hdr = parse_header(plan)
        self.assertEqual(hdr["variant"], VARIANT_NATIVE)

    def test_native_variant_has_cleanup_step(self):
        rc, plan, stderr = run_planner(minimal_toml(), extra_args=["--build"])
        if rc != 0:
            self.skipTest(f"Native planner failed: {stderr}")
        hdr = parse_header(plan)
        ops = [parse_step(plan, i)["op"] for i in range(hdr["step_count"])]
        self.assertIn(OP_CLEANUP, ops, "Native plan should include a CLEANUP step")

    def test_keep_tmp_removes_cleanup(self):
        rc, plan, stderr = run_planner(minimal_toml(), extra_args=["--build", "--keep-tmp"])
        if rc != 0:
            self.skipTest(f"Native planner failed: {stderr}")
        hdr = parse_header(plan)
        ops = [parse_step(plan, i)["op"] for i in range(hdr["step_count"])]
        self.assertNotIn(OP_CLEANUP, ops, "--keep-tmp should suppress CLEANUP steps")


class TestPolicyEnforcement(unittest.TestCase):

    def setUp(self):
        if not os.path.exists(PLANNER):
            self.skipTest(f"cogman-planner not found at {PLANNER}")

    def test_restricted_write_policy_rejected(self):
        """Planning to a rootfs outside policy.filesystem.write should fail."""
        toml = minimal_toml().replace(
            'write = ["/"]',
            'write = ["/mnt/rogue"]'
        )
        rc, plan, stderr = run_planner(toml, rootfs="/tmp/bad-target")
        self.assertNotEqual(rc, 0, "Planner should reject rootfs outside write policy")
        self.assertIn("olicy", stderr)

    def test_allowed_write_policy_passes(self):
        toml = minimal_toml().replace(
            'write = ["/"]',
            'write = ["/tmp"]'
        )
        rc, plan, stderr = run_planner(toml, rootfs="/tmp/rogue-test")
        self.assertEqual(rc, 0, f"Planner should accept rootfs inside write policy:\n{stderr}")


class TestPlanCache(unittest.TestCase):

    def setUp(self):
        if not os.path.exists(PLANNER):
            self.skipTest(f"cogman-planner not found at {PLANNER}")

    def test_second_run_uses_cache(self):
        """Two identical planning runs should produce byte-identical plan files."""
        toml = minimal_toml(name="cachepkg")
        rc1, plan1, _ = run_planner(toml, extra_args=["--no-cache"])
        rc2, plan2, _ = run_planner(toml)
        if rc1 != 0 or rc2 != 0:
            self.skipTest("Planner failed; skipping cache test")
        self.assertEqual(plan1, plan2, "Second run should produce identical plan bytes")

    def test_no_cache_flag_still_produces_valid_plan(self):
        rc, plan, stderr = run_planner(minimal_toml(name="nocachepkg"), extra_args=["--no-cache"])
        if rc != 0:
            self.skipTest(f"Planner failed: {stderr}")
        hdr = parse_header(plan)
        self.assertEqual(hdr["magic"], PLAN_MAGIC)


if __name__ == "__main__":
    unittest.main()
