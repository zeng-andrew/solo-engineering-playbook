"""Shared, standard-library-only helpers for SDLC project scripts."""

from __future__ import annotations

import re
import json
from datetime import date
from pathlib import Path
from typing import Mapping


SKILL_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = SKILL_ROOT / "assets" / "templates"
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
INTERACTIONS = ("coach", "collaborate", "fast")
RIGOR_LEVELS = ("light", "standard", "strict")
GIT_CHECKPOINT_POLICIES = ("off", "strict-only", "always")
TASK_FILES = ("intent.md", "spec.md", "plan.md", "verification.md")


def require_project(path: Path) -> Path:
    project = path.expanduser().resolve()
    if not project.exists():
        raise FileNotFoundError(f"Project path does not exist: {project}")
    if not project.is_dir():
        raise NotADirectoryError(f"Project path is not a directory: {project}")
    return project


def validate_slug(slug: str) -> str:
    if not SLUG_PATTERN.fullmatch(slug):
        raise ValueError(
            "Slug must contain lowercase letters, digits, and single hyphens only "
            "(example: user-login)."
        )
    return slug


def validate_title(title: str) -> str:
    title = title.strip()
    if not title:
        raise ValueError("Title must not be empty.")
    if any(character in title for character in ("\r", "\n")):
        raise ValueError("Title must be a single line.")
    return title


def yaml_string(value: str) -> str:
    """Return a JSON string, which is also a valid YAML double-quoted scalar."""
    return json.dumps(value, ensure_ascii=False)


def variables(**values: str) -> dict[str, str]:
    result = {"DATE": date.today().isoformat()}
    result.update(values)
    return result


def render(template_name: str, values: Mapping[str, str]) -> str:
    template_path = TEMPLATE_ROOT / template_name
    if not template_path.is_file():
        raise FileNotFoundError(f"Template is missing: {template_path}")
    content = template_path.read_text(encoding="utf-8")
    for key, value in values.items():
        content = content.replace("{{" + key + "}}", value)
    unresolved = re.findall(r"\{\{[A-Z0-9_]+\}\}", content)
    if unresolved:
        raise ValueError(
            f"Template {template_name} has unresolved variables: {', '.join(sorted(set(unresolved)))}"
        )
    return content


def create_if_missing(path: Path, content: str) -> bool:
    """Create a UTF-8 file without ever replacing an existing path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
    except FileExistsError:
        return False
    return True
