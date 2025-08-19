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
import textwrap


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
    manifest_path = None
    if os.name == "nt":
        manifest_xml = textwrap.dedent(
            """\
            <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
            <assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
              <assemblyIdentity version="1.0.0.0" processorArchitecture="*" name="KlaviyoSyncTool" type="win32"/>
              <description>Klaviyo Checkout Snapshot Sync Tool</description>
              <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
                <security>
                  <requestedPrivileges>
                    <requestedExecutionLevel level="asInvoker" uiAccess="false"/>
                  </requestedPrivileges>
                </security>
              </trustInfo>
              <dependency>
                <dependentAssembly>
                  <assemblyIdentity type="win32" name="Microsoft.Windows.Common-Controls" version="6.0.0.0" processorArchitecture="*" publicKeyToken="6595b64144ccf1df" language="*"/>
                </dependentAssembly>
              </dependency>
            </assembly>
            """
        ).strip()
        build_dir = Path("build")
        build_dir.mkdir(exist_ok=True)
        manifest_path = build_dir / "asInvoker.manifest"
        manifest_path.write_text(manifest_xml, encoding="utf-8")
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
    if manifest_path:
        args.extend(["--manifest", str(manifest_path)])
    args.append("klaviyo_gui/main.py")
    run_pyinstaller(args)


def build_cli():
    manifest_path = None
    if os.name == "nt":
        # Reuse the same manifest for CLI
        build_dir = Path("build")
        build_dir.mkdir(exist_ok=True)
        manifest_path = build_dir / "asInvoker.manifest"
        if not manifest_path.exists():
            manifest_path.write_text("""
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <assemblyIdentity version="1.0.0.0" processorArchitecture="*" name="klaviyo_fetch_metrics" type="win32"/>
  <description>Klaviyo CLI</description>
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel level="asInvoker" uiAccess="false"/>
      </requestedPrivileges>
    </security>
  </trustInfo>
  <dependency>
    <dependentAssembly>
      <assemblyIdentity type="win32" name="Microsoft.Windows.Common-Controls" version="6.0.0.0" processorArchitecture="*" publicKeyToken="6595b64144ccf1df" language="*"/>
    </dependentAssembly>
  </dependency>
</assembly>
""".strip(), encoding="utf-8")
    args = [
        "--noconfirm",
        "--clean",
        "--onefile",
        "--console",
        "--name",
        "klaviyo_fetch_metrics",
        "fetch_metrics.py",
    ]
    if manifest_path:
        args.extend(["--manifest", str(manifest_path)])
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


