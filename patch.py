#!/usr/bin/env python3
"""
Quick check: verifies frontend/package.json declares every dependency
actually imported across the codebase. Run from project ROOT.

This doesn't install anything — it just diffs "what's imported" against
"what's declared", so gaps like the react-router-dom one can be caught
before a build/CI run, not after.
"""
import os
import re
import json

ROOT = os.getcwd()
FRONTEND = os.path.join(ROOT, "frontend")
SRC = os.path.join(FRONTEND, "src")
PKG_JSON = os.path.join(FRONTEND, "package.json")

# Packages that are always fine to ignore (relative imports, css, vite env)
IGNORE_PREFIXES = (".", "/", "@/")

def find_imports():
    pkgs = set()
    pattern = re.compile(r"""(?:from\s+|import\s+)['"]([^'"]+)['"]""")
    for dirpath, _, files in os.walk(SRC):
        for fname in files:
            if not fname.endswith((".js", ".jsx")):
                continue
            with open(os.path.join(dirpath, fname), encoding="utf-8") as f:
                content = f.read()
            for match in pattern.findall(content):
                if match.startswith(IGNORE_PREFIXES):
                    continue
                # Normalize scoped packages: '@tanstack/react-query' stays as-is,
                # but 'react-dom/client' -> 'react-dom'
                parts = match.split("/")
                if match.startswith("@"):
                    pkg = "/".join(parts[:2])
                else:
                    pkg = parts[0]
                pkgs.add(pkg)
    return pkgs

def main():
    if not os.path.isfile(PKG_JSON):
        print(f"❌  {PKG_JSON} not found")
        return

    with open(PKG_JSON, encoding="utf-8") as f:
        pkg_data = json.load(f)

    declared = set(pkg_data.get("dependencies", {}).keys()) | set(
        pkg_data.get("devDependencies", {}).keys()
    )
    imported = find_imports()

    missing = sorted(imported - declared)

    print("=" * 60)
    print("Frontend dependency check")
    print("=" * 60)
    print(f"Declared in package.json : {len(declared)} packages")
    print(f"Imported across src/     : {len(imported)} packages")
    print()

    if missing:
        print("❌  MISSING from package.json (imported but not declared):")
        for m in missing:
            print(f"   - {m}")
        print()
        print("Fix with:")
        print(f"   npm install {' '.join(missing)}")
    else:
        print("✅  Every imported package is declared in package.json.")

if __name__ == "__main__":
    main()
