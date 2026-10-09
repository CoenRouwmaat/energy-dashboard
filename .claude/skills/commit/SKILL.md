---
name: commit
description: Group the working-tree changes into atomic Conventional Commits that follow this repo's conventions (changelog-ready messages, issue references, prek hooks). Never pushes.
disable-model-invocation: true
argument-hint: "[paths or hint]"
allowed-tools: Bash(.claude/skills/commit/scripts/context.sh), Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(git add:*), Bash(git apply --cached:*), Bash(git restore --staged:*), Bash(git commit:*)
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "$CLAUDE_PROJECT_DIR/.claude/skills/commit/scripts/guard.sh"
---

# Commit

Invoking this skill authorizes one thing: committing the current changes on the current branch. Don't push, amend, tag, switch branches or discard changes. Never use `--no-verify`.

A `PreToolUse` hook ([scripts/guard.sh](scripts/guard.sh)) enforces this for Bash commands you run directly: it blocks `--no-verify`, `--amend`, `commit -a`, broad staging (`git add -A`, `.`, `-u`, `-f`), `git push`, `reset --hard`, `clean`, and `git restore` without `--staged`. If it blocks something, do not look for a way around it; report it.

## Scripts

Run from the repo root. Each prints its reason on failure.

| Script | Step | Exit codes |
|---|---|---|
| `scripts/context.sh` | 1 | 0 changes to commit, 1 abort, 2 working tree clean |

Follow the commit conventions in [CLAUDE.md](../../../CLAUDE.md). `Co-Authored-By` trailer as given in the session's attribution instructions.

## 1. Snapshot

Run `.claude/skills/commit/scripts/context.sh`. It is read-only and prints the branch, status, the diff vs `HEAD` (`uv.lock` as a stat only), new files as diffs, and recent commits.

- Exit 2: nothing to commit. Say so and stop.
- Exit 1: stop and report its message (detached HEAD, or on `main`).
- `SENSITIVE` lines: never stage those paths. Mention them in the summary.
- `STAGED` lines: something was staged before the skill ran. Treat it as a hint about the intended grouping, not as a commit you must make as-is (see step 3).

If the user passed an argument, paths restrict the scope (leave everything else uncommitted and say so); any other text is a hint about intent or grouping.

## 2. Plan

Group the changes into **atomic units**. Each unit has one purpose, can be reverted on its own, and maps to exactly one type:

- `feat`, `fix`, `refactor` for code; `test` for tests; `docs`; `style` for formatting-only changes; `chore` for deps, config and tooling.
- Don't mix formatting, deps or docs into a feature commit. A feature and its tests are two commits (`feat` then `test`) unless they are inseparable.
- If everything is genuinely one unit, one commit is correct; don't split artificially.
- Order the commits so each one leaves the repo working.

Print the plan as text first. For each commit give the exact commit message (full subject, plus body lines if any, as it will be committed) and a short explanation of what each file added or changed in that commit does (one line per file or per small group of files, not just a bare path list). Flag any new scope. Then **ask once for all commits together** with `AskUserQuestion` (e.g. Approve / Change something); don't ask in plain chat and don't ask per commit. Commit nothing before approval. Treat "Other" text as an instruction and show the revised plan again. If a grouping or type is a real judgement call, or a file's hunks belong to different units and cannot be split cleanly, put that in the same question instead of guessing.

### Message

`<type>(<scope>): <description>`, subject at most 72 characters, imperative mood, lower case, no trailing period.

- **Changelog-ready**: commit messages become changelog lines (see CLAUDE.md), so describe the user-visible effect (`add retry on rate-limited requests`), not the file touched (`update client.py`).
- **Scope** is the area touched: `ned` for the NED client, its docs and tests; `claude` for `.claude/` skills and config; omit it for repo-wide changes (deps, tooling, README-wide edits). Match the recent commits.
- **New scopes**: when the changes introduce a new component worth tracking on its own in the changelog (a new package or module such as a dashboard UI, a new data source client, a storage layer), use a new short lower-case scope named after it (e.g. `dashboard`, `db`) without asking. Look at the directory layout and `git log` for scopes already in use first, and reuse an existing one when it fits. Don't create a scope for a single file, a one-off change, or a name that overlaps an existing scope. Flag every new scope in the plan and in the final summary, so CLAUDE.md's scope note ("currently `ned`") can be updated.
- **Breaking** changes get `!` (`feat(ned)!: ...`) and a body line saying what breaks and how to migrate.
- **Issues**: add `Closes #N` in the body only for the commit that completes the issue. For feature or fix work, check what is underway with `.claude/skills/start-issues/scripts/candidates.sh | grep ^IN_PROGRESS`. If unsure whether a commit completes an issue, leave the reference out.
- Don't add a body otherwise; the subject is enough.

## 3. Commit each unit

For every unit, in order:

1. Make the index match the unit exactly: `git add -- <paths>` for explicit paths only. Check `git diff --cached --name-only` and unstage extras with `git restore --staged -- <paths>`. To split one file's hunks across units, write a trimmed patch to the scratchpad directory and `git apply --cached` it (`git add -p` is interactive and not available); if that is not workable, ask.
2. Commit with one `-m` per paragraph, trailer last, so no heredoc is needed:
   `git commit -m "<subject>" -m "Closes #N" -m "Co-Authored-By: ..."` (omit the `Closes` paragraph when there is none).

### Handling prek failures

Hooks run on commit ([prek.toml](../../../prek.toml): ruff check/format, ty, whitespace, toml). pytest is not a hook and this skill does not run it.

- Hooks that auto-fix files (formatting, whitespace, `ruff --fix`): re-stage the fixes and retry the commit once. The fixes belong in the same commit.
- Real failures (ty errors, ruff violations that cannot be auto-fixed, check-toml errors): stop immediately. Report each failing hook with its output and the message that failed. Leave commits made so far in place and the remaining units uncommitted. Don't retry a second time and don't fix the code yourself.

## 4. Summarise

Show the commits made (`git log --oneline -<n>`, `<n>` = commits made in this run) and `git status --short` for anything left uncommitted, with the reason (restricted scope, `SENSITIVE`, hook failure). Name any new scope introduced in this run. End by noting that nothing was pushed.
