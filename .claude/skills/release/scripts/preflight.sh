#!/usr/bin/env bash
# Release preflight. Exit 0 = OK to proceed; exit 1 = abort (reason on stderr).
# Read-only apart from `git fetch` and any auto-fixes prek applies to the working tree.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

fail() {
    echo "preflight FAILED: $1" >&2
    exit 1
}

[ "$(git branch --show-current)" = "dev" ] || fail "not on branch 'dev'"

git fetch --quiet --tags origin || fail "git fetch failed"

if git rev-parse --verify --quiet origin/dev >/dev/null; then
    [ "$(git rev-list --count HEAD..origin/dev)" = "0" ] || fail "dev is behind origin/dev; pull first"
else
    echo "note: origin/dev does not exist yet (first push)"
fi
[ "$(git rev-list --count HEAD..origin/main)" = "0" ] || fail "origin/main has commits that dev lacks; resolve before releasing"

gh auth status >/dev/null 2>&1 || fail "gh is not authenticated"
open_prs=$(gh pr list --head dev --base main --state open --json number --jq 'length')
[ "$open_prs" = "0" ] || fail "a release PR from dev to main is already open"

last_tag=$(git describe --tags --abbrev=0 2>/dev/null || true)
if [ -n "$last_tag" ]; then
    commits=$(git rev-list --count "$last_tag"..HEAD)
else
    commits=$(git rev-list --count HEAD)
fi
dirty=$(git status --porcelain | wc -l | tr -d ' ')
if [ "$commits" = "0" ] && [ "$dirty" = "0" ]; then
    fail "nothing to release since ${last_tag:-the beginning}"
fi

uv run pytest -q || fail "pytest failed"

# prek can auto-fix files, which also makes it exit non-zero. Retry once if it changed the tree.
before=$(git diff | shasum)
if ! uv run prek run --all-files; then
    after=$(git diff | shasum)
    if [ "$before" != "$after" ]; then
        echo "note: prek auto-fixed files; re-running to confirm"
        uv run prek run --all-files || fail "prek still failing after auto-fix"
        echo "note: auto-fixes are uncommitted and belong in the pending-work commit plan"
    else
        fail "prek reported problems (see output above)"
    fi
fi

echo "preflight OK (last tag: ${last_tag:-none}, commits since: $commits, uncommitted files: $dirty)"
