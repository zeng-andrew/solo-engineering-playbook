#!/usr/bin/env python3
"""Validate .sdlc structure and optionally require resolved work-item content."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from _common import (
    GIT_CHECKPOINT_POLICIES,
    INTERACTIONS,
    RIGOR_LEVELS,
    SLUG_PATTERN,
    TASK_FILES,
    require_project,
)


UNRESOLVED_PATTERN = re.compile(r"<!--\s*待讨论(?:\s*[:：][\s\S]*?)?\s*-->")
FRONTMATTER_SLUG = re.compile(r"^slug:\s*([^\s]+)\s*$", re.MULTILINE)


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checked_tasks: int = 0


def _read(path: Path, report: Report) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        report.errors.append(f"Cannot read UTF-8 file {path}: {exc}")
        return ""


def _config_value(content: str, key: str) -> Optional[str]:
    match = re.search(rf"^{re.escape(key)}:\s*([^#\s]+)", content, re.MULTILINE)
    return match.group(1).strip('"\'') if match else None


def validate(project_path: Path, strict: bool = False) -> Report:
    project = require_project(project_path)
    report = Report()
    root = project / ".sdlc"
    config_path = root / "config.yaml"
    lessons_path = root / "lessons.md"
    tasks_root = root / "tasks"
    decisions_root = root / "decisions"

    for directory in (root, tasks_root, decisions_root):
        if not directory.is_dir():
            report.errors.append(f"Missing directory: {directory}")
    for file_path in (config_path, lessons_path):
        if not file_path.is_file():
            report.errors.append(f"Missing file: {file_path}")

    if config_path.is_file():
        config = _read(config_path, report)
        interaction = _config_value(config, "interaction")
        rigor = _config_value(config, "rigor")
        git_checkpoints = _config_value(config, "git_checkpoints")
        if interaction not in INTERACTIONS:
            report.errors.append(
                f"config.yaml interaction must be one of {', '.join(INTERACTIONS)}; got {interaction!r}"
            )
        if rigor not in RIGOR_LEVELS:
            report.errors.append(
                f"config.yaml rigor must be one of {', '.join(RIGOR_LEVELS)}; got {rigor!r}"
            )
        if git_checkpoints is not None and git_checkpoints not in GIT_CHECKPOINT_POLICIES:
            report.errors.append(
                "config.yaml git_checkpoints must be one of "
                f"{', '.join(GIT_CHECKPOINT_POLICIES)}; got {git_checkpoints!r}"
            )

    if tasks_root.is_dir():
        for task_dir in sorted(path for path in tasks_root.iterdir() if path.is_dir()):
            if task_dir.name.startswith("."):
                report.warnings.append(f"Temporary work-item directory remains: {task_dir}")
                continue
            report.checked_tasks += 1
            if not SLUG_PATTERN.fullmatch(task_dir.name):
                report.errors.append(f"Invalid work-item slug directory: {task_dir}")
            for filename in TASK_FILES:
                path = task_dir / filename
                if not path.is_file():
                    report.errors.append(f"Missing work-item file: {path}")
                    continue
                content = _read(path, report)
                slug_match = FRONTMATTER_SLUG.search(content)
                if not slug_match or slug_match.group(1) != task_dir.name:
                    report.errors.append(f"Frontmatter slug does not match directory in {path}")
                unresolved_count = len(UNRESOLVED_PATTERN.findall(content))
                if unresolved_count:
                    message = f"{path} contains {unresolved_count} unresolved discussion marker(s)"
                    (report.errors if strict else report.warnings).append(message)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a project's .sdlc memory.")
    parser.add_argument("--project", type=Path, default=Path.cwd(), help="Project directory")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat unresolved discussion markers as errors",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = validate(args.project, args.strict)
    except (FileNotFoundError, NotADirectoryError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    for message in report.warnings:
        print(f"warning: {message}")
    for message in report.errors:
        print(f"error: {message}", file=sys.stderr)
    print(
        f"Checked {report.checked_tasks} work item(s): "
        f"{len(report.errors)} error(s), {len(report.warnings)} warning(s)."
    )
    return 1 if report.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
