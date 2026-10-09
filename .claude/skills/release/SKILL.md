---
name: release
description: Cut a release of energy-dashboard. Commits pending work, updates docs, bumps the version, updates the changelog, and opens a dev -> main PR that closes the related issues. `/release finish` tags and publishes after the PR is merged.
disable-model-invocation: true
argument-hint: "[version | finish]"
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "$CLAUDE_PROJECT_DIR/.claude/skills/release/scripts/guard.sh"
---

# Release

Two modes, chosen by the argument:

- `/release` or `/release 0.3.0`: prepare the release and open the PR (steps 1-8). An explicit version overrides the computed one.
- `/release finish`: after the PR is merged, tag and publish (step 9).

Invoking this skill authorizes: committing, pushing `dev`, creating the PR, and (in `finish`) pushing the tag and creating the GitHub release. Nothing beyond that. Never use `--no-verify`, never force-push, never touch `main` directly.

A `PreToolUse` hook ([scripts/guard.sh](scripts/guard.sh)) enforces this for Bash commands you run directly: it blocks `--no-verify`, force-pushes, pushes to or from `main`, manual `git tag`, `gh release create` and `gh pr merge`. If it blocks something, do not look for a way around it; report it. The hook stays active for the rest of the session once the skill has been invoked.

## Scripts

The deterministic steps are scripts in [scripts/](scripts/), run from the repo root. Run them instead of retyping their commands. Each prints its reason on failure and exits non-zero.

| Script | Step | Exit codes |
|---|---|---|
| `preflight.sh` | 1 | 0 OK, 1 abort |
| `collect-issues.sh` | 7 | 0 OK, 1 a referenced issue does not exist |
| `finish.sh [--dry-run]` | 9 | 0 done, 1 aborted |

Every approval gate below (steps 2, 6, 8 and the `finish` run in step 9) is asked with the `AskUserQuestion` tool (e.g. Approve / Change something), after printing the thing to approve as text. Don't ask for approval in plain chat.

Follow the commit conventions in [CLAUDE.md](../../../CLAUDE.md): atomic, conventional, `Co-Authored-By` trailer as given in the session's attribution instructions.

## 1. Preflight

Run `.claude/skills/release/scripts/preflight.sh`. On a non-zero exit, stop and report its message.

It checks: on `dev` and not behind `origin/dev` or `origin/main`; `gh` authenticated; no release PR already open; something to release since the last tag; pytest passes (pytest is not a prek hook, so this is the only place it is gated); `prek run --all-files` passes. If prek auto-fixed files, the script says so; those fixes are uncommitted and go into the step 2 commit plan.

## 2. Commit pending work

If `git status` is clean, skip. Otherwise:

1. Group the changes into atomic conventional commits. Never stage `.env` or anything gitignored; if a change cannot be grouped confidently, ask.
2. **Show the plan (files and message per commit) and ask for approval** before committing anything.
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
3. **Show the rewritten entry and ask for approval.**
4. Commit `CHANGELOG.md` as `chore(release): prepare for v<version>`.

## 7. Collect issues

Run `.claude/skills/release/scripts/collect-issues.sh`. It reads `Closes|Fixes|Resolves #N` from commit messages since the last tag and prints:

- `CLOSES #N <OPEN|CLOSED> <title>`: issues to close. Report any that are already `CLOSED` and leave them out of the PR body. Exit 1 means a referenced issue does not exist: stop.
- `UNREFERENCED #N <title>`: "In Progress" on the "Energy dashboard" project but no commit references it. Warning only; do not close these.

## 8. Push and open the PR

1. Before pushing, print a summary: version, commits included, the changelog entry, and the issues that will be closed. **Ask for approval.**
2. `git push origin dev`.
3. `gh pr create --base main --head dev --title "release: v<version>"`. The body contains the changelog entry, then one `Closes #N` line per verified issue, and ends with the PR attribution line from the session's attribution instructions.
4. Open the PR in the browser with `gh pr view --web`, output the PR URL and remind the user to merge with a **merge commit** (not squash), then run `/release finish`.

### Handling prek failures (applies to every commit above)

- Hooks that auto-fix files (formatting, whitespace, `ruff --fix`): re-stage the fixes and retry the commit once. A change from format-only fixes belongs in the same commit.
- Real failures (ty errors, ruff violations that cannot be auto-fixed, check-toml errors): stop immediately. Report each failing hook with its output. Do not push or open a PR. Leave commits made so far in place.

## 9. `/release finish`

Run `.claude/skills/release/scripts/finish.sh --dry-run` first and show the output (tag, commit, release notes), then run `.claude/skills/release/scripts/finish.sh` once the user agrees (ask with `AskUserQuestion`).

The script verifies the release PR is merged, tags the PR's merge commit (not whatever `main` points at now) with the version read from `pyproject.toml` at that commit, pushes the tag, creates the GitHub release with that version's `CHANGELOG.md` section as notes, fast-forwards `dev` to `origin/main`, and prints the state of each issue the PR closes.

If it aborts, report the reason. A failed fast-forward means the PR was probably squash-merged: tell the user, and do not reset `dev` yourself. Report any linked issue that is not `CLOSED`.
