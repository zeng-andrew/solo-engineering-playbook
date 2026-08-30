#!/usr/bin/env python3
"""Create one work-item artifact set atomically and refuse duplicate slugs."""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

from _common import (
    TASK_FILES,
    render,
    require_project,
    validate_slug,
    validate_title,
    variables,
    yaml_string,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a new .sdlc work item.")
    parser.add_argument("--project", type=Path, default=Path.cwd(), help="Project directory")
    parser.add_argument("--slug", required=True, help="Lowercase hyphenated identifier")
    parser.add_argument("--title", required=True, help="Human-readable title")
    return parser.parse_args()


def create_work_item(project_path: Path, slug: str, title: str) -> Path:
    project = require_project(project_path)
    slug = validate_slug(slug)
    title = validate_title(title)

    sdlc_root = project / ".sdlc"
    if not (sdlc_root / "config.yaml").is_file():
        raise FileNotFoundError(
            f"{sdlc_root / 'config.yaml'} is missing. Run init_project.py first."
        )
    tasks_root = sdlc_root / "tasks"
    tasks_root.mkdir(parents=True, exist_ok=True)
    destination = tasks_root / slug
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite existing work item: {destination}")

    values = variables(SLUG=slug, TITLE=title, TITLE_YAML=yaml_string(title))
    temporary = Path(tempfile.mkdtemp(prefix=f".{slug}-", dir=tasks_root))
    try:
        for filename in TASK_FILES:
            content = render(filename, values)
            with (temporary / filename).open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(content)
        temporary.rename(destination)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return destination


def main() -> int:
    args = parse_args()
    try:
        destination = create_work_item(args.project, args.slug, args.title)
    except (FileExistsError, FileNotFoundError, NotADirectoryError, ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"Created work item: {destination}")
    print("Start with intent.md and discussion; do not fill product decisions by assumption.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
