#!/usr/bin/env python3
"""Scan all profiles for stale feishu-table-card plugin versions.

Usage (from execute_code or terminal):
    python ~/.hermes/skills/productivity/s-feishu-card-v1/scripts/scan_plugin_versions.py

Prints a table of plugin line counts across all profiles.
If any profile differs from the main agent, flags it as STALE.
"""

import os
from pathlib import Path

def main():
    home = Path.home() / ".hermes"
    main_plugin = home / "plugins" / "feishu-table-card" / "__init__.py"

    if not main_plugin.exists():
        print("ERROR: Main agent plugin not found at", main_plugin)
        return

    main_lines = sum(1 for _ in open(main_plugin, encoding="utf-8"))

    profiles_dir = home / "profiles"
    if not profiles_dir.exists():
        print("No profiles directory found.")
        return

    print(f"{'Profile':<20} {'Lines':<8} {'Status'}")
    print("-" * 42)
    print(f"{'[main agent]':<20} {main_lines:<8} REFERENCE")
    print("-" * 42)

    stale_profiles = []

    for profile_dir in sorted(profiles_dir.iterdir()):
        if not profile_dir.is_dir():
            continue
        plugin_file = profile_dir / "plugins" / "feishu-table-card" / "__init__.py"
        if plugin_file.exists():
            lines = sum(1 for _ in open(plugin_file, encoding="utf-8"))
            status = "OK" if lines == main_lines else "STALE"
            if status == "STALE":
                stale_profiles.append(profile_dir.name)
            print(f"{profile_dir.name:<20} {lines:<8} {status}")
        else:
            print(f"{profile_dir.name:<20} {'N/A':<8} NO_PLUGIN")

    print()
    if stale_profiles:
        print(f"STALE PROFILES DETECTED: {', '.join(stale_profiles)}")
        print("Fix: copy main agent plugin to each stale profile, clear __pycache__, restart gateway.")
        print()
        print("Quick fix command:")
        print("  for p in " + " ".join(stale_profiles) + "; do")
        print("    cp ~/.hermes/plugins/feishu-table-card/__init__.py ~/.hermes/profiles/$p/plugins/feishu-table-card/__init__.py")
        print("    rm -rf ~/.hermes/profiles/$p/plugins/feishu-table-card/__pycache__")
        print("  done")
    else:
        print("All profiles are in sync with main agent plugin.")

if __name__ == "__main__":
    main()
