from __future__ import annotations

import re
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "skills" / "solo-engineering-coach"
SCRIPTS = SKILL / "scripts"
INSTALLER = REPO / "scripts" / "install_skill.py"
TASK_FILES = ("intent.md", "spec.md", "plan.md", "verification.md")
UNRESOLVED = re.compile(r"<!--\s*待讨论(?:\s*[:：][\s\S]*?)?\s*-->")


def run_script(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=REPO,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
        env=environment,
    )


class WorkflowScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project = Path(self.temp_dir.name) / "示例项目"
        self.project.mkdir()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def init(self) -> subprocess.CompletedProcess[str]:
        return run_script(
            SCRIPTS / "init_project.py",
            "--project",
            str(self.project),
            "--interaction",
            "coach",
            "--rigor",
            "standard",
        )

    def new_item(
        self, slug: str = "user-login", title: str = "用户登录"
    ) -> subprocess.CompletedProcess[str]:
        return run_script(
            SCRIPTS / "new_work_item.py",
            "--project",
            str(self.project),
            "--slug",
            slug,
            "--title",
            title,
        )

    def test_init_is_idempotent_and_preserves_existing_config(self) -> None:
        first = self.init()
        self.assertEqual(first.returncode, 0, first.stderr)
        config = self.project / ".sdlc" / "config.yaml"
        original = config.read_text(encoding="utf-8")
        self.assertIn("interaction: coach", original)
        self.assertIn("rigor: standard", original)
        self.assertIn("git_checkpoints: strict-only", original)

        sentinel = original + "\nuser_note: keep-this\n"
        config.write_text(sentinel, encoding="utf-8")
        second = self.init()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(config.read_text(encoding="utf-8"), sentinel)
        self.assertIn("preserved:", second.stdout)

    def test_new_item_renders_all_templates_and_rejects_duplicate(self) -> None:
        self.assertEqual(self.init().returncode, 0)
        first = self.new_item(title='用户 "登录"')
        self.assertEqual(first.returncode, 0, first.stderr)
        task = self.project / ".sdlc" / "tasks" / "user-login"
        for filename in TASK_FILES:
            content = (task / filename).read_text(encoding="utf-8")
            self.assertIn("slug: user-login", content)
            self.assertIn('用户 "登录"', content)
            self.assertNotRegex(content, r"\{\{[A-Z0-9_]+\}\}")

        duplicate = self.new_item()
        self.assertEqual(duplicate.returncode, 2)
        self.assertIn("Refusing to overwrite", duplicate.stderr)

    def test_new_item_rejects_invalid_slug(self) -> None:
        self.assertEqual(self.init().returncode, 0)
        result = self.new_item("Bad Slug")
        self.assertEqual(result.returncode, 2)
        self.assertIn("Slug must contain", result.stderr)

    def test_verifier_warns_normally_and_fails_strict_until_resolved(self) -> None:
        self.assertEqual(self.init().returncode, 0)
        self.assertEqual(self.new_item().returncode, 0)

        normal = run_script(
            SCRIPTS / "verify_project.py", "--project", str(self.project)
        )
        self.assertEqual(normal.returncode, 0, normal.stderr)
        self.assertIn("warning:", normal.stdout)

        strict = run_script(
            SCRIPTS / "verify_project.py", "--project", str(self.project), "--strict"
        )
        self.assertEqual(strict.returncode, 1)
        self.assertIn("unresolved discussion marker", strict.stderr)

        task = self.project / ".sdlc" / "tasks" / "user-login"
        for filename in TASK_FILES:
            path = task / filename
            resolved = UNRESOLVED.sub("已确认", path.read_text(encoding="utf-8"))
            path.write_text(resolved, encoding="utf-8")
        completed = run_script(
            SCRIPTS / "verify_project.py", "--project", str(self.project), "--strict"
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("0 error(s)", completed.stdout)

    def test_verifier_detects_missing_artifact_and_slug_mismatch(self) -> None:
        self.assertEqual(self.init().returncode, 0)
        self.assertEqual(self.new_item().returncode, 0)
        task = self.project / ".sdlc" / "tasks" / "user-login"
        (task / "plan.md").unlink()
        spec = task / "spec.md"
        spec.write_text(
            spec.read_text(encoding="utf-8").replace("slug: user-login", "slug: wrong"),
            encoding="utf-8",
        )
        result = run_script(
            SCRIPTS / "verify_project.py", "--project", str(self.project)
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("Missing work-item file", result.stderr)
        self.assertIn("Frontmatter slug does not match", result.stderr)

    def test_verifier_rejects_invalid_git_checkpoint_policy(self) -> None:
        self.assertEqual(self.init().returncode, 0)
        config = self.project / ".sdlc" / "config.yaml"
        config.write_text(
            config.read_text(encoding="utf-8").replace(
                "git_checkpoints: strict-only",
                "git_checkpoints: every-step",
            ),
            encoding="utf-8",
        )
        result = run_script(
            SCRIPTS / "verify_project.py", "--project", str(self.project)
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("git_checkpoints must be one of", result.stderr)


class InstallationTests(unittest.TestCase):
    def test_installer_copies_refuses_and_backs_up(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "agent-skills"
            first = run_script(INSTALLER, "--target", str(target))
            self.assertEqual(first.returncode, 0, first.stderr)
            installed = target / "solo-engineering-coach"
            self.assertTrue((installed / "SKILL.md").is_file())

            marker = installed / "local-marker.txt"
            marker.write_text("old installation", encoding="utf-8")
            refused = run_script(INSTALLER, "--target", str(target))
            self.assertEqual(refused.returncode, 2)
            self.assertTrue(marker.is_file())

            replaced = run_script(INSTALLER, "--target", str(target), "--replace")
            self.assertEqual(replaced.returncode, 0, replaced.stderr)
            self.assertFalse(marker.exists())
            backups = list(target.glob("solo-engineering-coach.bak-*"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(
                (backups[0] / "local-marker.txt").read_text(encoding="utf-8"),
                "old installation",
            )

    def test_installer_refuses_to_replace_canonical_source(self) -> None:
        result = run_script(INSTALLER, "--target", str(SKILL.parent), "--replace")
        self.assertEqual(result.returncode, 2)
        self.assertIn("canonical source", result.stderr)
        self.assertTrue((SKILL / "SKILL.md").is_file())


class SkillPackageTests(unittest.TestCase):
    def test_frontmatter_name_and_description(self) -> None:
        content = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
        self.assertIsNotNone(match)
        frontmatter = match.group(1)
        self.assertRegex(frontmatter, r"(?m)^name: solo-engineering-coach$")
        self.assertRegex(frontmatter, r"(?m)^description: .+")

    def test_all_local_markdown_links_resolve(self) -> None:
        checked = 0
        for document in REPO.rglob("*.md"):
            if ".git" in document.parts:
                continue
            content = document.read_text(encoding="utf-8")
            for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", content):
                if link.startswith(("http://", "https://", "#")):
                    continue
                target = link.split("#", 1)[0]
                self.assertTrue((document.parent / target).resolve().exists(), f"{document}: {link}")
                checked += 1
        self.assertGreaterEqual(checked, 6)

    def test_templates_and_references_are_nonempty_and_no_scaffold_todos(self) -> None:
        required = [
            SKILL / "references" / "conversation-protocol.md",
            SKILL / "references" / "modes-and-risk.md",
            SKILL / "references" / "artifact-contracts.md",
            SKILL / "references" / "git-checkpoints.md",
            SKILL / "references" / "portability.md",
        ]
        required.extend((SKILL / "assets" / "templates").glob("*"))
        for path in required:
            content = path.read_text(encoding="utf-8")
            self.assertGreater(len(content.strip()), 80, str(path))
            self.assertNotRegex(content, r"(?i)\bTODO\b|replace me|placeholder")


if __name__ == "__main__":
    unittest.main()
