import unittest
import os
import shutil
import subprocess
import textwrap
from tests.utils.plan_reader import PlanReader

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PLANNER_BIN = os.path.join(ROOT, "cogman", "planner", "target", "debug", "cogman-planner")
CASE_DIR = os.path.join(ROOT, "tests", "graph", "cases")
OUT_PLAN = os.path.join(ROOT, "tests", "graph", "out.plan")

class TestGraph(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.path.exists(CASE_DIR):
            shutil.rmtree(CASE_DIR)
        os.makedirs(CASE_DIR, exist_ok=True)
        # Create metadata dir for planner convention
        os.makedirs(os.path.join(CASE_DIR, "metadata"), exist_ok=True)
        
    def create_pkg(self, name, deps=None, category="base"):
        # structure: metadata/category/name/name.toml
        cat_dir = os.path.join(CASE_DIR, "metadata", category)
        pkg_dir = os.path.join(cat_dir, name)
        os.makedirs(pkg_dir, exist_ok=True)
        
        dep_str = ""
        if deps:
            q_deps = [f'"{d}"' for d in deps]
            dep_str = f'[identity.depends]\nbuild = [{", ".join(q_deps)}]'
            
        toml = f"""
        [identity]
        name = "{name}"
        version = "1.0"
        category = "{category}"
        summary = "test"
        
        [identity.source]
        kind = "tarball"
        file = "{name}.tar"
        
        {dep_str}
        
        [build]
        system = "make"
        steps = ["echo build {name}"]
        
        [installer]
        steps = ["echo install {name}"]
        """
        toml = textwrap.dedent(toml).strip()
        
        target_file = os.path.join(pkg_dir, f"{name}.toml")
        with open(target_file, "w") as f:
            f.write(toml)
        return target_file

    def run_planner(self, target_pkg, cwd):
        cmd = [PLANNER_BIN, "build", target_pkg, "-o", OUT_PLAN]
        return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)

    def test_linear_deps(self):
        # A -> B
        self.create_pkg("libB")
        pkgA = self.create_pkg("pkgA", deps=["base/libB"])
        
        res = self.run_planner(pkgA, CASE_DIR)
        self.assertEqual(res.returncode, 0, f"Planner failed: {res.stderr}")
        reader = PlanReader(OUT_PLAN)
        
        # Binary plan: fetch/extract/install. We check for presence of pkg names in commands.
        cmds = [s.cmd for s in reader.steps]
        
        self.assertTrue(any("libB" in c for c in cmds), "libB missing")
        self.assertTrue(any("pkgA" in c for c in cmds), "pkgA missing")
        
        # Verify order: libB must be processed before pkgA
        idx_B = next(i for i, c in enumerate(cmds) if "libB" in c)
        idx_A = next(i for i, c in enumerate(cmds) if "pkgA" in c)
        self.assertLess(idx_B, idx_A, f"libB should be before pkgA: {cmds}")

    def test_cycle_detection(self):
        # A -> B -> A
        self.create_pkg("cycB", deps=["base/cycA"])
        pkgA = self.create_pkg("cycA", deps=["base/cycB"])
        
        res = self.run_planner(pkgA, CASE_DIR)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("cycle detected", res.stderr)

    def test_deep_chain(self):
        # A -> B -> C
        self.create_pkg("libC")
        self.create_pkg("libB", deps=["base/libC"])
        pkgA = self.create_pkg("pkgA", deps=["base/libB"])
        
        res = self.run_planner(pkgA, CASE_DIR)
        self.assertEqual(res.returncode, 0, f"Planner failed: {res.stderr}")
        
        reader = PlanReader(OUT_PLAN)
        cmds = [s.cmd for s in reader.steps]
        
        # Verify all 3 present
        self.assertTrue(any("libC" in c for c in cmds), "libC missing")
        self.assertTrue(any("libB" in c for c in cmds), "libB missing")
        self.assertTrue(any("pkgA" in c for c in cmds), "pkgA missing")
        
        # Verify order: libC -> libB -> pkgA
        idx_C = next(i for i, c in enumerate(cmds) if "libC" in c)
        idx_B = next(i for i, c in enumerate(cmds) if "libB" in c)
        idx_A = next(i for i, c in enumerate(cmds) if "pkgA" in c)
        
        self.assertLess(idx_C, idx_B, "libC must be before libB")
        self.assertLess(idx_B, idx_A, "libB must be before pkgA")
