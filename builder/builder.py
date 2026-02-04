from pathlib import Path
import shutil
import subprocess

from core.log.voice import info, ok, err
from core.executor import run


class BuildError(SystemExit):
    """Raised when a build step fails."""
    pass


# ─────────────────────────────────────────────
# Directory preparation
# ─────────────────────────────────────────────

def _clean_dir(path: Path):
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def prepare_pkgroot(pkg_path: Path) -> Path:
    """
    Clean and recreate the pkgroot directory.
    """
    pkgroot = pkg_path / "pkgroot"
    info("Preparing the package root with due care, sir.")
    _clean_dir(pkgroot)
    return pkgroot


# ─────────────────────────────────────────────
# Environment
# ─────────────────────────────────────────────

def build_environment(pkgroot: Path) -> dict:
    """
    Base environment for all build and install commands.
    """
    env = dict(subprocess.os.environ)
    env["PKGROOT"] = str(pkgroot.resolve())
    env["DESTDIR"] = str(pkgroot.resolve())
    return env


# ─────────────────────────────────────────────
# Step execution
# ─────────────────────────────────────────────

def run_steps(steps: list[str], *, cwd: Path, env: dict, role: str):
    """
    Execute steps sequentially for a given role.
    """
    for step in steps:
        info(f"[{role}] Executing step")
        run(step, cwd=cwd, env=env)


# ─────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────

def build_package(package: str, pkg_path: Path, metadata: dict):
    """
    Build and install a package using builder + installer roles.

    Order:
      1. builder.steps
      2. installer.steps
    """

    info(f"Commencing build procedure for '{package}', sir.")

    builder = metadata.get("builder", {})
    installer = metadata.get("installer", {})

    builder_steps = builder.get("steps")
    installer_steps = installer.get("steps")

    if not builder_steps:
        err(f"No builder steps defined for {package}")
        raise BuildError(1)

    if not installer_steps:
        err(f"No installer steps defined for {package}")
        raise BuildError(1)

    # Prepare pkgroot
    pkgroot = prepare_pkgroot(pkg_path)
    env = build_environment(pkgroot)

    info("Builder phase commencing, sir.")
    run_steps(
        builder_steps,
        cwd=pkg_path,
        env=env,
        role="BUILDER",
    )

    info("Installer phase commencing, sir.")
    run_steps(
        installer_steps,
        cwd=pkg_path,
        env=env,
        role="INSTALLER",
    )

    ok(f"Build completed successfully for '{package}'. A commendable performance, sir.")
