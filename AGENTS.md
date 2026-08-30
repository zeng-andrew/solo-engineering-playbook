# Repository Instructions

This repository maintains the portable `solo-engineering-coach` skill.

- Treat `skills/solo-engineering-coach/` as the single source of truth. Keep agent-specific adapters thin and do not duplicate the core workflow in them.
- Keep the core skill independent of proprietary APIs, hooks, IDE features, and subagent support.
- Use Python standard library only for shipped scripts unless a future change explicitly revises this portability promise.
- Preserve existing user files by default. New scripts must refuse destructive overwrites or require an explicit flag with a recoverable backup.
- When behavior changes, update the relevant reference/template and add or adjust an observable test.
- Run `python -m unittest discover -s tests -v` and the skill package validator before handing off changes.
