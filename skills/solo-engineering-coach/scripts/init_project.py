#!/usr/bin/env python3
"""Initialize a project's .sdlc directory without overwriting existing files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _common import (
    GIT_CHECKPOINT_POLICIES,
    INTERACTIONS,
    RIGOR_LEVELS,
    create_if_missing,
    render,
    require_project,
    variables,
    yaml_string,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize portable .sdlc project memory.")
    parser.add_argument("--project", type=Path, default=Path.cwd(), help="Project directory")
    parser.add_argument("--interaction", choices=INTERACTIONS, default="coach")
    parser.add_argument("--rigor", choices=RIGOR_LEVELS, default="standard")
    parser.add_argument(
        "--git-checkpoints",
        choices=GIT_CHECKPOINT_POLICIES,
        default="strict-only",
        help="Git checkpoint policy",
    )
    return parser.parse_args()


def initialize(
    project_path: Path,
    interaction: str,
    rigor: str,
    git_checkpoints: str,
) -> tuple[list[Path], list[Path]]:
    project = require_project(project_path)
    if interaction not in INTERACTIONS:
        raise ValueError(f"Unsupported interaction mode: {interaction}")
    if rigor not in RIGOR_LEVELS:
        raise ValueError(f"Unsupported rigor level: {rigor}")
    if git_checkpoints not in GIT_CHECKPOINT_POLICIES:
        raise ValueError(f"Unsupported Git checkpoint policy: {git_checkpoints}")

    root = project / ".sdlc"
    (root / "tasks").mkdir(parents=True, exist_ok=True)
    (root / "decisions").mkdir(parents=True, exist_ok=True)
    values = variables(
        PROJECT_NAME_YAML=yaml_string(project.name),
        INTERACTION=interaction,
        RIGOR=rigor,
        GIT_CHECKPOINTS=git_checkpoints,
    )
    candidates = {
        root / "config.yaml": render("config.yaml", values),
        root / "lessons.md": render("lessons.md", values),
    }
    created: list[Path] = []
    preserved: list[Path] = []
    for path, content in candidates.items():
        (created if create_if_missing(path, content) else preserved).append(path)
    return created, preserved


def main() -> int:
    args = parse_args()
    try:
        created, preserved = initialize(
            args.project,
            args.interaction,
            args.rigor,
            args.git_checkpoints,
        )
    except (FileNotFoundError, NotADirectoryError, ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    for path in created:
        print(f"created: {path}")
    for path in preserved:
        print(f"preserved: {path}")
    print("SDLC project memory is ready. Existing files were not overwritten.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
