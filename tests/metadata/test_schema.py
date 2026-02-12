import unittest
import os
import sys
import subprocess
import shutil
import textwrap

# Paths
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PLANNER_BIN = os.path.join(ROOT, "cogman", "src", "planner", "target", "debug", "cogman-planner")
CASE_DIR = os.path.join(ROOT, "tests", "metadata", "cases")

class TestSchema(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.path.exists(CASE_DIR):
            shutil.rmtree(CASE_DIR)
        os.makedirs(CASE_DIR, exist_ok=True)

    def run_planner(self, toml_content):
        # Dedent and strip
        toml_content = textwrap.dedent(toml_content).strip()
        
        # Write tmp file
        case_id = self._testMethodName
        path = os.path.join(CASE_DIR, f"{case_id}.toml")
        with open(path, "w") as f:
            f.write(toml_content)
            
        cmd = [PLANNER_BIN, "build", path, "-o", "/dev/null"]
        # Capture stdout/stderr
        return subprocess.run(cmd, capture_output=True, text=True)

    def assertFiles(self, result, expected_err=None):
        if expected_err:
            self.assertNotEqual(result.returncode, 0, f"Expected failures for {expected_err}")
            self.assertIn(expected_err, result.stderr)
        else:
            self.assertEqual(result.returncode, 0, f"Expected success: {result.stderr}")

    def base_toml(self):
        return """
        [identity]
        name = "pkg"
        version = "1.0"
        category = "base"
        summary = "test"
        
        [identity.source]
        kind = "tarball"
        file = "pkg.tar.xz"
        
        [build]
        system = "make"
        steps = ["echo build"]
        
        [installer]
        steps = ["echo install"]
        """

    # --- Identity Tests ---
    def test_missing_identity(self):
        toml = """
        [build]
        steps = []
        """
        # "missing field `identity`" or "missing field `system`" depending on parse order
        # Actually, if identity is missing, TOML parser might complain about next field keys?
        # The error log says: missing field `system` at line 1 [build]
        self.assertFiles(self.run_planner(toml), "missing field")

    def test_missing_name(self):
        toml = """
        [identity]
        version = "1.0"
        """
        self.assertFiles(self.run_planner(toml), "missing field `name`")

    def test_bad_version_type(self):
        toml = self.base_toml().replace('version = "1.0"', 'version = 1.0')
        self.assertFiles(self.run_planner(toml), "invalid type: float")

    # --- Builder Tests ---
    def test_missing_build(self):
        toml = self.base_toml().replace('[build]', '#[build]')
        # [build] vs [builder] in struct. Error says "missing field `build`".
        self.assertFiles(self.run_planner(toml), "missing field `build`")

    def test_bad_steps_type(self):
        toml = self.base_toml().replace('steps = ["echo build"]', 'steps = "echo build"')
        self.assertFiles(self.run_planner(toml), "invalid type: string")

    # --- Installer Tests ---
    def test_missing_installer(self):
        toml = """
        [identity]
        name = "p"
        version = "1"
        category = "c"
        summary = "s"
        [identity.source]
        kind = "tarball"
        file = "f"
        [build]
        system = "make"
        steps = []
        """
        self.assertFiles(self.run_planner(toml), "missing field `installer`")

    # --- Schema Validation ---
    def test_unknown_field_root(self):
        toml = self.base_toml() + '\nextra = "foo"'
        self.assertFiles(self.run_planner(toml), None)

    def test_empty_steps(self):
        toml = self.base_toml().replace('steps = ["echo build"]', 'steps = []')
        # Validation logic in validate.rs forbids empty steps.
        # So this should FAIL.
        res = self.run_planner(toml)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("steps.commands must not be empty", res.stderr)

if __name__ == '__main__':
    unittest.main()
