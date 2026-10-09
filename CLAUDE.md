# CLAUDE.md

Solo project, not deployed. See [README.md](README.md) for the overview and
[docs/ned_client.md](docs/ned_client.md) for client usage; this file only covers conventions.

## Stack

- Python 3.14 (`requires-python >= 3.14`), managed with **uv**. Always `uv run ...` / `uv add ...`; never call `pip` or a bare `python`.
- pydantic v2 + pydantic-settings for models and config, `httpx` for HTTP.
- Lint/format with **ruff**, type-check with **ty** (not mypy/pyright). Tests with pytest.
- `NedClient` is **async** (`httpx.AsyncClient`): `async with`, `await`, `async for`. Tests use `httpx.MockTransport` + `asyncio.run` (no pytest-asyncio).
- Datetimes must be timezone-aware (ruff DTZ rules are enforced, including in tests).

## Checks

Hooks are managed by **prek** (not pre-commit), configured in [prek.toml](prek.toml): `uv run prek run --all-files`.
It runs ruff check/format and ty. Run pytest yourself; it is not a hook.

## Git workflow

- Day-to-day work goes directly on the `dev` branch. `main` only holds stable versions.
- Feature branches (deleted after merge) are merged with a **squash** commit; plain `dev` work is not squashed.
- Commits are **atomic** and follow **Conventional Commits** (`feat(ned): ...`, `fix:`, `docs:`, `test:`, `style:`, `chore:`). One logical change per commit: don't mix formatting, deps or docs into a feature commit.
- Scope is the area touched (currently `ned`); omit it for repo-wide changes.
- Mark breaking changes with `!` (`feat(ned)!: ...`); git-cliff renders them as **breaking**.
- Reference issues with `Closes #N` in the commit body. Work is tracked on the GitHub project "Energy dashboard" (statuses such as In Progress); use `gh` for it.
- Don't push unless asked.

## Changelog

[CHANGELOG.md](CHANGELOG.md) is generated with **git-cliff** ([cliff.toml](cliff.toml)) from commit messages, so
commit messages are user-facing: write them so they read well as a changelog line.
`style`, `test`, `docs` and `chore` commits end up in their own groups, so use the right type.
Changelog entries are rewritten by hand into prose after generation (see the 0.1.0 entry).
Releases go through the `/release` skill ([.claude/skills/release/SKILL.md](.claude/skills/release/SKILL.md)):
release commits use `chore(release): prepare for vX.Y.Z`, which `cliff.toml` skips. While pre-1.0, breaking changes bump the minor version.
Release PRs (`dev` -> `main`) are merged with a **merge commit**, not a squash.
