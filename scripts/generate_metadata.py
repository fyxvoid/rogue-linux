#!/usr/bin/env python3
"""
Cogman Metadata Generator
Generates production-grade metadata for ~1000 Linux packages.
Run from project root: python3 scripts/generate_metadata.py
"""
import os
import shutil
from pathlib import Path

METADATA_ROOT = Path(__file__).resolve().parent.parent / "metadata"

# ═══════════════════════════════════════════════════════════
# YAML TEMPLATES
# ═══════════════════════════════════════════════════════════

def identity_yaml(name, version, category, summary, src_file, src_kind="tarball", deps=None):
    lines = [
        f"name: {name}",
        f'version: "{version}"',
        f"category: {category}",
        "",
        f"summary: >",
        f"  {summary}",
        "",
        "source:",
        f"  kind: {src_kind}",
        f"  file: {src_file}",
    ]
    if deps:
        lines += ["", "depends:", "  build:"]
        for d in deps:
            lines.append(f"    - {d}")
    return "\n".join(lines) + "\n"


def builder_yaml(name, version, src_file, build_sys="autotools", flags="", src_dir=None):
    if src_dir is None:
        base = src_file.rsplit(".tar", 1)[0] if ".tar" in src_file else src_file.rsplit(".", 1)[0]
        src_dir = base
    steps = ['steps:', '  - rm -rf source build', '  - mkdir -p source build', '']

    ext_cmd = f'tar -xf tar/{src_file} -C source'
    steps += [
        '  - |',
        f'      echo "[COGMAN] Extracting {name} source, sir."',
        f'      {ext_cmd}',
        '',
    ]

    if build_sys == "autotools":
        cfg = f"../source/{src_dir}/configure --prefix=/usr"
        if flags:
            flags = flags.replace("--prefix=/usr", "").strip()
            cfg += " \\\n        " + flags.replace(" --", " \\\n        --")
        steps += [
            '  - |',
            f'      echo "[COGMAN] Configuring {name}, sir."',
            '      cd build',
            f'      {cfg}',
            '',
        ]
    elif build_sys == "cmake":
        cfg = f"cmake ../source/{src_dir} -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_BUILD_TYPE=Release"
        if flags:
            cfg += " \\\n        " + flags.replace(" -D", " \\\n        -D")
        steps += [
            '  - |',
            f'      echo "[COGMAN] Configuring {name} with CMake, sir."',
            '      cd build',
            f'      {cfg}',
            '',
        ]
    elif build_sys == "meson":
        cfg = f"meson setup ../source/{src_dir} . --prefix=/usr --buildtype=release"
        if flags:
            cfg += " " + flags
        steps += [
            '  - |',
            f'      echo "[COGMAN] Configuring {name} with Meson, sir."',
            '      cd build',
            f'      {cfg}',
            '',
        ]
    elif build_sys == "python":
        steps += [
            '  - |',
            f'      echo "[COGMAN] Building {name} Python package, sir."',
            f'      cd source/{src_dir}',
            '      python3 setup.py build',
            '',
        ]
    elif build_sys == "go":
        steps += [
            '  - |',
            f'      echo "[COGMAN] Building {name} with Go, sir."',
            f'      cd source/{src_dir}',
            '      go build -o ../../build/ ./...',
            '',
        ]
    elif build_sys == "rust":
        steps += [
            '  - |',
            f'      echo "[COGMAN] Building {name} with Cargo, sir."',
            f'      cd source/{src_dir}',
            '      cargo build --release',
            '',
        ]
    elif build_sys == "make":
        steps += [
            '  - |',
            f'      echo "[COGMAN] Building {name}, sir."',
            f'      cd source/{src_dir}',
            '      make -j$(nproc)' + (f' {flags}' if flags else ''),
            '',
        ]
    elif build_sys == "ninja":
        steps += [
            '  - |',
            f'      echo "[COGMAN] Building {name} with Ninja, sir."',
            '      cd build',
            '      ninja',
            '',
        ]

    return "\n".join(steps) + "\n"


def installer_yaml(name, build_sys="autotools"):
    if build_sys in ("autotools", "cmake", "make"):
        return (
            "steps:\n"
            "  - |\n"
            f'      echo "[COGMAN] Building {name}, sir."\n'
            "      cd build\n"
            "      make -j$(nproc)\n"
            "\n"
            "  - |\n"
            f'      echo "[COGMAN] Installing {name} into staging root, sir."\n'
            "      cd build\n"
            '      make install DESTDIR="$PKGROOT"\n'
        )
    elif build_sys == "meson" or build_sys == "ninja":
        return (
            "steps:\n"
            "  - |\n"
            f'      echo "[COGMAN] Building {name}, sir."\n'
            "      cd build\n"
            "      ninja\n"
            "\n"
            "  - |\n"
            f'      echo "[COGMAN] Installing {name} into staging root, sir."\n'
            "      cd build\n"
            '      DESTDIR="$PKGROOT" ninja install\n'
        )
    elif build_sys == "python":
        return (
            "steps:\n"
            "  - |\n"
            f'      echo "[COGMAN] Installing {name} Python package, sir."\n'
            f"      cd source/{name}*\n"
            '      python3 setup.py install --root="$PKGROOT" --prefix=/usr\n'
        )
    elif build_sys == "go":
        return (
            "steps:\n"
            "  - |\n"
            f'      echo "[COGMAN] Installing {name}, sir."\n'
            '      install -Dm755 build/* "$PKGROOT/usr/bin/"\n'
        )
    elif build_sys == "rust":
        return (
            "steps:\n"
            "  - |\n"
            f'      echo "[COGMAN] Installing {name}, sir."\n'
            f"      cd source/{name}*\n"
            '      install -Dm755 target/release/{name} "$PKGROOT/usr/bin/"\n'
        )
    return (
        "steps:\n"
        "  - |\n"
        f'      echo "[COGMAN] Installing {name}, sir."\n'
        "      cd build\n"
        '      make install DESTDIR="$PKGROOT"\n'
    )


def policy_yaml(write=None, net=False, caps=None):
    w = write or ["/usr"]
    lines = ["filesystem:", "  read:", "    - /", "  write:"]
    for p in w:
        lines.append(f"    - {p}")
    lines += ["", "network:", f"  outbound: {'true' if net else 'false'}", ""]
    if caps:
        lines.append("capabilities:")
        for c in caps:
            lines.append(f"  - {c}")
    else:
        lines.append("capabilities: []")
    return "\n".join(lines) + "\n"


# ═══════════════════════════════════════════════════════════
# PACKAGE DEFINITION HELPER
# ═══════════════════════════════════════════════════════════

def P(name, ver, cat, summary, deps=None, build="autotools", flags="",
      net=False, caps=None, write=None, src_kind="tarball", ext=".tar.xz"):
    """Create a compact package definition dict."""
    return {
        "name": name, "version": ver, "category": cat,
        "summary": summary, "deps": deps or [],
        "build": build, "flags": flags,
        "net": net, "caps": caps, "write": write,
        "src_kind": src_kind,
        "src_file": f"{name}-{ver}{ext}",
    }


# ═══════════════════════════════════════════════════════════
# GENERATION ENGINE
# ═══════════════════════════════════════════════════════════

def generate_package(pkg):
    """Generate all 4 metadata files for a package."""
    cat = pkg["category"]
    name = pkg["name"]
    pkg_dir = METADATA_ROOT / cat / name / "metadata"
    pkg_dir.mkdir(parents=True, exist_ok=True)

    # identity.yaml
    (pkg_dir / "identity.yaml").write_text(
        identity_yaml(name, pkg["version"], cat, pkg["summary"],
                      pkg["src_file"], pkg["src_kind"], pkg["deps"])
    )

    # builder.yaml
    (pkg_dir / "builder.yaml").write_text(
        builder_yaml(name, pkg["version"], pkg["src_file"],
                     pkg["build"], pkg["flags"])
    )

    # installer.yaml
    (pkg_dir / "installer.yaml").write_text(
        installer_yaml(name, pkg["build"])
    )

    # policy.yaml
    (pkg_dir / "policy.yaml").write_text(
        policy_yaml(pkg.get("write"), pkg["net"], pkg.get("caps"))
    )


def main():
    # Import all package definitions
    from pkg_data import ALL_PACKAGES

    print(f"[COGMAN] Generating metadata for {len(ALL_PACKAGES)} packages, sir.")

    count = 0
    for pkg in ALL_PACKAGES:
        generate_package(pkg)
        count += 1

    total_files = count * 4
    print(f"[COGMAN] Generated {total_files} metadata files for {count} packages. Quite satisfactory, sir.")


if __name__ == "__main__":
    main()
