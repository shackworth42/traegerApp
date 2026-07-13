#!/usr/bin/env python3
"""
dev.py - One-file helper for pulling this project onto a new machine and
pushing your work back to GitHub when you're done for the day.

This script has no third-party dependencies (only the Python standard
library) and only requires that `git` is installed and on your PATH. It is
meant to be usable *before* the repo is cloned - e.g. saved to your Desktop
or Documents folder and run with plain `python dev.py ...` - and it also
lives inside the repo itself once cloned, so you can keep using this same
copy from within your working directory.

Commands
--------
clone   Clone the repo to your machine and open it in VS Code.
push    Stage, commit, and push every local change ("end of day" sync).

Examples
--------
    python dev.py clone
    python dev.py clone --dir ~/projects/traegerApp
    python dev.py push
    python dev.py push -m "Fixed idle screen flicker"
"""

import argparse
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_URL = "https://github.com/shackworth42/traegerApp.git"
DEFAULT_BRANCH = "main"
DEFAULT_CLONE_DIR_NAME = "traegerApp"


def run(cmd, cwd=None, check=True):
    """Run a command, echoing it first so you can see exactly what's happening."""
    print(f"$ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=cwd, check=check)


def find_repo_root(start: Path) -> Path:
    """Walk upward from `start` looking for a .git directory."""
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise SystemExit(
        "Could not find a git repository. Run `python dev.py clone` first, "
        "or run `push` from inside the cloned project."
    )


def clone(args: argparse.Namespace) -> None:
    dest = Path(args.dir).expanduser().resolve()

    if dest.exists() and any(dest.iterdir()):
        if (dest / ".git").exists():
            print(f"'{dest}' already looks like a git repo — pulling latest changes instead of cloning.")
            run(["git", "pull", "origin", args.branch], cwd=dest)
        else:
            raise SystemExit(
                f"Destination '{dest}' already exists and is not empty. "
                "Choose a different --dir, or remove that folder first."
            )
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        run(["git", "clone", "--branch", args.branch, REPO_URL, str(dest)])

    print(f"\nRepo ready at: {dest}")

    if not args.no_open:
        code_cli = shutil.which("code")
        if code_cli:
            run([code_cli, str(dest)])
        else:
            print(
                "Couldn't find the 'code' command on your PATH, so VS Code wasn't opened "
                "automatically.\nIn VS Code, run \"Shell Command: Install 'code' command "
                "in PATH\" from the Command Palette to enable this next time.\n"
                f"For now, open the folder manually: {dest}"
            )


def push(args: argparse.Namespace) -> None:
    repo_root = find_repo_root(Path.cwd())

    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=repo_root, capture_output=True, text=True, check=True
    )
    if not status.stdout.strip():
        print("Nothing to commit — working tree is already clean.")
        return

    run(["git", "add", "-A"], cwd=repo_root)

    message = args.message or f"End of day sync - {datetime.now():%Y-%m-%d %H:%M}"
    run(["git", "commit", "-m", message], cwd=repo_root)

    branch = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root, capture_output=True, text=True, check=True
    ).stdout.strip()

    run(["git", "push", "-u", "origin", branch], cwd=repo_root)
    print(f"\nAll changes pushed to origin/{branch}.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Helper for cloning and syncing the traegerApp repo.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    clone_parser = subparsers.add_parser("clone", help="Clone the repo and open it in VS Code.")
    clone_parser.add_argument(
        "--dir", default=DEFAULT_CLONE_DIR_NAME,
        help=f"Where to clone the repo (default: ./{DEFAULT_CLONE_DIR_NAME}).",
    )
    clone_parser.add_argument(
        "--branch", default=DEFAULT_BRANCH, help=f"Branch to clone/pull (default: {DEFAULT_BRANCH}).",
    )
    clone_parser.add_argument(
        "--no-open", action="store_true", help="Don't try to open the folder in VS Code afterwards.",
    )
    clone_parser.set_defaults(func=clone)

    push_parser = subparsers.add_parser("push", help="Stage, commit, and push all local changes.")
    push_parser.add_argument(
        "-m", "--message", default=None, help="Commit message (default: auto-generated timestamp message).",
    )
    push_parser.set_defaults(func=push)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except subprocess.CalledProcessError as exc:
        print(f"\nCommand failed with exit code {exc.returncode}.", file=sys.stderr)
        sys.exit(exc.returncode)


if __name__ == "__main__":
    main()
