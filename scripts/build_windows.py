#!/usr/bin/env python3
"""
Build Windows single-file executables for the Klaviyo tools using PyInstaller.

Outputs:
  - dist/KlaviyoSyncTool.exe (GUI)
  - dist/klaviyo_fetch_metrics.exe (CLI)

Run on Windows:
  python scripts/build_windows.py
"""

import os
import sys
import importlib
from pathlib import Path


def run_pyinstaller(args: list[str]) -> None:
    try:
        import PyInstaller.__main__ as pyimain
    except Exception as e:
        print("PyInstaller is not installed. Install with: pip install pyinstaller", file=sys.stderr)
        raise
    print("Running:", " ".join(["pyinstaller"] + args))
    pyimain.run(args)


def find_customtkinter_assets() -> tuple[str, str] | None:
    """Return (src, dest) for --add-data to include customtkinter assets, or None if not found."""
    try:
        ctk = importlib.import_module("customtkinter")
        pkg_path = Path(ctk.__path__[0])
        assets = pkg_path / "assets"
        if assets.exists():
            dest = "customtkinter/assets"
            sep = os.pathsep  # On Windows, ";"; on POSIX, ":"
            return str(assets), dest
    except Exception:
        pass
    return None


def build_gui():
    add_data = find_customtkinter_assets()
    args = [
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name",
        "KlaviyoSyncTool",
    ]
    if add_data:
        args.append(f"--add-data={add_data[0]}{os.pathsep}{add_data[1]}")
    args.append("klaviyo_gui/main.py")
    run_pyinstaller(args)


def build_cli():
    args = [
        "--noconfirm",
        "--clean",
        "--onefile",
        "--console",
        "--name",
        "klaviyo_fetch_metrics",
        "fetch_metrics.py",
    ]
    run_pyinstaller(args)


def main() -> None:
    # Ensure working directory is repo root
    repo_root = Path(__file__).resolve().parents[1]
    os.chdir(repo_root)
    print("Working directory:", os.getcwd())

    build_gui()
    build_cli()
    print("\nBuild complete. Artifacts in dist/.")


if __name__ == "__main__":
    main()


