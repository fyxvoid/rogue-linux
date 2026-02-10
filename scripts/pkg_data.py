#!/usr/bin/env python3
"""Aggregates all package definitions into ALL_PACKAGES."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from pkg_core import ALL_PACKAGES as CORE
from pkg_networking import ALL_PACKAGES as NET
from pkg_security1 import ALL_PACKAGES as SEC1
from pkg_security2 import ALL_PACKAGES as SEC2
from pkg_security3 import ALL_PACKAGES as SEC3
from pkg_extra import ALL_PACKAGES as EXTRA

ALL_PACKAGES = CORE + NET + SEC1 + SEC2 + SEC3 + EXTRA

if __name__ == "__main__":
    print(f"Total packages defined: {len(ALL_PACKAGES)}")
    print(f"Expected metadata files: {len(ALL_PACKAGES) * 4}")
    # Check for duplicate names within same category
    seen = {}
    for p in ALL_PACKAGES:
        key = f"{p['category']}/{p['name']}"
        if key in seen:
            print(f"WARNING: Duplicate package: {key}")
        seen[key] = True
