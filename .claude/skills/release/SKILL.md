---
name: release
description: Cut a release of energy-dashboard. Commits pending work, updates docs, bumps the version, updates the changelog, and opens a dev -> main PR that closes the related issues. `/release finish` tags and publishes after the PR is merged.
disable-model-invocation: true
argument-hint: "[version | finish]"
---

# Release

Two modes, chosen by the argument:

- `/release` or `/release 0.3.0`: prepare the release and open the PR (steps 1-8). An explicit version overrides the computed one.
- `/release finish`: after the PR is merged, tag and publish (step 9).

Invoking this skill authorizes: committing, pushing `dev`, creating the PR, and (in `finish`) pushing the tag and creating the GitHub release. Nothing beyond that. Never use `--no-verify`, never force-push, never touch `main` directly.

Follow the commit conventions in [CLAUDE.md](../../../CLAUDE.md): atomic, conventional, `Co-Authored-By` trailer as given in the session's attribution instructions.

## 1. Preflight (abort on any failure, with the reason)

- Current branch is `dev`; `git fetch` shows it is not behind `origin/dev` or `origin/main` (if `main` has commits `dev` lacks, stop and ask).
- `gh auth status` succeeds; no open PR from `dev` to `main` already exists (`gh pr list --head dev --base main`).
- `uv run pytest` passes. Pytest is not a prek hook, so this is the only place it is gated.
- `uv run prek run --all-files` passes (see step 8 for how failures are handled).
- There is something to release: `git-cliff --unreleased` is non-empty.

## 2. Commit pending work

If `git status` is clean, skip. Otherwise:

1. Group the changes into atomic conventional commits. Never stage `.env` or anything gitignored; if a change cannot be grouped confidently, ask.
2. **Show the plan (files and message per commit) and wait for approval** before committing anything.
3. Commit as approved.

## 3. Determine the version

- Computed: `uv run git-cliff --bumped-version` (strip the leading `v`). While pre-1.0, `cliff.toml` bumps breaking changes as minor.
- If the user passed a version, use it instead and say it overrides the computed one.
- State the version, the previous tag, and the reason (feat / breaking / fix) before continuing. Refuse a version that is not greater than the latest tag.

## 4. Update docs

Scope: `docs/`, `README.md`, `CLAUDE.md`. Not notebooks.

Compare them with the code and the commits since the last tag (`git log <last-tag>..HEAD`) and edit only what is stale: usage examples, commands, project layout, conventions. Do not rewrite for style. Commit as `docs: ...`. Skip the commit if nothing changed.

## 5. Bump the version

`uv version <version>` (updates `pyproject.toml` and `uv.lock`), then `uv sync`. Commit `pyproject.toml` and `uv.lock` as `chore(release): prepare for v<version>`.

That exact prefix is skipped by `cliff.toml`, so the release commits stay out of the changelog.

## 6. Update the changelog

1. `uv run git-cliff --unreleased --tag v<version> --prepend CHANGELOG.md` (the `<!-- git-cliff: end of header -->` marker in `CHANGELOG.md` is required for `--prepend`).
2. Rewrite the new entry by hand into the style of the 0.1.0 entry: a one-line summary, then grouped bullets in prose that describe user-visible effect, not raw commit subjects. Call out breaking changes explicitly with migration hints.
3. **Show the rewritten entry and wait for approval.**
4. Commit `CHANGELOG.md` as `chore(release): prepare for v<version>`.

## 7. Collect issues

- Gather issue numbers from `Closes|Fixes|Resolves #N` in commit messages since the last tag.
- Verify each with `gh issue view N`: it must exist and be open. Report any that are already closed.
- Also list issues that are "In Progress" on the "Energy dashboard" project but not referenced by any commit, as a warning only; do not close them.

## 8. Push and open the PR

1. Before pushing, print a summary: version, commits included, the changelog entry, and the issues that will be closed. **Wait for approval.**
2. `git push origin dev`.
3. `gh pr create --base main --head dev --title "release: v<version>"`. The body contains the changelog entry, then one `Closes #N` line per verified issue, and ends with the PR attribution line from the session's attribution instructions.
4. Output the PR URL and remind the user to merge with a **merge commit** (not squash), then run `/release finish`.

### Handling prek failures (applies to every commit above)

- Hooks that auto-fix files (formatting, whitespace, `ruff --fix`): re-stage the fixes and retry the commit once. A change from format-only fixes belongs in the same commit.
- Real failures (ty errors, ruff violations that cannot be auto-fixed, check-toml errors): stop immediately. Report each failing hook with its output. Do not push or open a PR. Leave commits made so far in place.

## 9. `/release finish`

1. Verify the release PR for `dev` is merged (`gh pr list --head dev --base main --state merged`), otherwise abort.
2. `git fetch`, then tag the merge commit on `origin/main`: `git tag -a v<version> origin/main -m "v<version>"`, where the version is read from `pyproject.toml` on `main`. Push the tag.
3. `gh release create v<version> --title "v<version>" --notes <that version's section from CHANGELOG.md>`.
4. Fast-forward `dev` to `main` (`git merge --ff-only origin/main`; it should be a fast-forward because the PR was merged with a merge commit). If it is not, report it and stop.
5. Confirm the linked issues are closed and report any that are not.
