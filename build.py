#!/usr/bin/env python3
"""
Cross-platform build script for Memory Card Game.
Detects the OS and runs PyInstaller with the correct settings.

Usage:
    python build.py              # Build the executable
    python build.py --clean      # Clean build artifacts first
    python build.py --run        # Build and then run the game
"""

import subprocess
import sys
import os
import shutil
import platform
import argparse

GAME_NAME = "MemoryCardGame"
MAIN_SCRIPT = "main.py"
ASSETS_DIR = "assets"

# All source files that PyInstaller should include as hidden imports
SOURCE_FILES = [
    "game.py",
    "ui_controls.py",
    "asset_state.py",
    "ai_logic.py",
    "physics_collision.py",
    "backgrounds.py",
    "highscores.py",
]


def get_sep():
    """Return the correct path separator for --add-data based on OS."""
    if platform.system() == "Windows":
        return ";"
    return ":"


def check_dependencies():
    """Ensure pygame and pyinstaller are installed."""
    print("Checking dependencies...")
    try:
        import pygame
        print(f"  pygame: {pygame.ver}")
    except ImportError:
        print("  pygame not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pygame"])

    try:
        import PyInstaller
        print(f"  pyinstaller: {PyInstaller.__version__}")
    except ImportError:
        print("  pyinstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])


def clean_build():
    """Remove old build artifacts."""
    print("Cleaning build artifacts...")
    for d in ["build", "dist"]:
        if os.path.exists(d):
            shutil.rmtree(d)
            print(f"  Removed {d}/")
    for f in [f"{GAME_NAME}.spec"]:
        if os.path.exists(f):
            os.remove(f)
            print(f"  Removed {f}")


def build():
    """Run PyInstaller to create the executable."""
    sep = get_sep()
    assets_data = f"{ASSETS_DIR}{sep}{ASSETS_DIR}"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onedir",
        "--windowed",
        "--noconfirm",
        f"--add-data={assets_data}",
        f"--name={GAME_NAME}",
        MAIN_SCRIPT,
    ]

    # Add source files as hidden imports so PyInstaller finds them
    for src in SOURCE_FILES:
        module = src.replace(".py", "")
        cmd.append(f"--hidden-import={module}")

    print(f"\nBuilding {GAME_NAME}...")
    print(f"  Command: {' '.join(cmd)}\n")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"\nERROR: Build failed with exit code {result.returncode}")
        sys.exit(1)

    # Determine output path
    if platform.system() == "Windows":
        exe_path = os.path.join("dist", GAME_NAME, f"{GAME_NAME}.exe")
    elif platform.system() == "Darwin":
        exe_path = os.path.join("dist", f"{GAME_NAME}.app")
    else:
        exe_path = os.path.join("dist", GAME_NAME, GAME_NAME)

    print(f"\n{'='*50}")
    print(f"  Build complete!")
    print(f"  Output: {os.path.abspath(exe_path)}")
    print(f"{'='*50}")
    return exe_path


def run_game(exe_path):
    """Run the built executable."""
    if platform.system() == "Darwin":
        # On macOS, run the app via open command
        subprocess.Popen(["open", exe_path])
    else:
        subprocess.Popen([exe_path])


def main():
    parser = argparse.ArgumentParser(description=f"Build {GAME_NAME}")
    parser.add_argument("--clean", action="store_true", help="Clean build artifacts first")
    parser.add_argument("--run", action="store_true", help="Run the game after building")
    args = parser.parse_args()

    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    check_dependencies()

    if args.clean:
        clean_build()

    exe_path = build()

    if args.run:
        print("\nLaunching game...")
        run_game(exe_path)


if __name__ == "__main__":
    main()
