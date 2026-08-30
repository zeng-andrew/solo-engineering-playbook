#!/usr/bin/env python3
"""Install the canonical skill into an arbitrary agent skill directory."""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


SKILL_NAME = "solo-engineering-coach"


def source_skill() -> Path:
    return Path(__file__).resolve().parents[1] / "skills" / SKILL_NAME


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy solo-engineering-coach into an agent's skill directory."
    )
    parser.add_argument("--target", required=True, type=Path, help="Agent skills directory")
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Back up an existing installation, then install the repository version",
    )
    return parser.parse_args()


def install(target_root: Path, replace: bool = False) -> tuple[Path, Optional[Path]]:
    source = source_skill()
    if not (source / "SKILL.md").is_file():
        raise RuntimeError(f"Canonical skill is missing: {source}")

    target_root = target_root.expanduser().resolve()
    destination = target_root / SKILL_NAME
    try:
        destination.resolve().relative_to(source.resolve())
    except ValueError:
        pass
    else:
        raise RuntimeError("Install target must not be the canonical source or a child of it.")
    target_root.mkdir(parents=True, exist_ok=True)
    backup = None

    if destination.exists():
        if not replace:
            raise FileExistsError(
                f"Refusing to overwrite existing installation: {destination}. "
                "Use --replace to create a backup and continue."
            )
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = target_root / f"{SKILL_NAME}.bak-{stamp}"
        suffix = 1
        while backup.exists():
            backup = target_root / f"{SKILL_NAME}.bak-{stamp}-{suffix}"
            suffix += 1
        destination.rename(backup)

    try:
        shutil.copytree(
            source,
            destination,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
        )
    except Exception:
        if destination.is_dir():
            shutil.rmtree(destination)
        elif destination.exists():
            destination.unlink()
        if backup is not None:
            backup.rename(destination)
        raise
    return destination, backup


def main() -> int:
    args = parse_args()
    try:
        destination, backup = install(args.target, args.replace)
    except (FileExistsError, RuntimeError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"Installed {SKILL_NAME} to {destination}")
    if backup:
        print(f"Previous installation backed up to {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
