#!/usr/bin/env bash
# Finish a release after the dev -> main PR was merged: tag the PR's merge commit, push the tag,
# create the GitHub release from the CHANGELOG section, and fast-forward dev to main.
#
# Usage: finish.sh [--dry-run]
# Exit 0 = done; exit 1 = aborted (reason on stderr). --dry-run prints the mutating commands instead of running them.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

DRY_RUN=0
[ "${1:-}" = "--dry-run" ] && DRY_RUN=1

fail() {
    echo "finish FAILED: $1" >&2
    exit 1
}

run() {
    if [ "$DRY_RUN" = "1" ]; then
        echo "[dry-run] $*"
    else
        "$@"
    fi
}

git fetch --quiet --tags origin || fail "git fetch failed"

# The most recently merged release PR from dev to main.
pr=$(gh pr list --head dev --base main --state merged --limit 1 --json number,mergeCommit --jq '.[0] // empty')
[ -n "$pr" ] || fail "no merged PR from dev to main found; merge the release PR first"
pr_number=$(jq -r .number <<<"$pr")
merge_sha=$(jq -r .mergeCommit.oid <<<"$pr")
[ -n "$merge_sha" ] && [ "$merge_sha" != "null" ] || fail "PR #$pr_number has no merge commit"
git cat-file -e "$merge_sha^{commit}" 2>/dev/null || fail "merge commit $merge_sha not found locally after fetch"
git merge-base --is-ancestor "$merge_sha" origin/main || fail "merge commit $merge_sha is not on origin/main"

# Version comes from the merged code, not from whatever main looks like now.
version=$(git show "$merge_sha:pyproject.toml" | sed -n 's/^version = "\(.*\)"$/\1/p' | head -1)
[ -n "$version" ] || fail "could not read version from pyproject.toml at $merge_sha"
tag="v$version"
git rev-parse --verify --quiet "refs/tags/$tag" >/dev/null && fail "tag $tag already exists"

# This version's section of CHANGELOG.md, up to the next "## [" heading.
notes=$(git show "$merge_sha:CHANGELOG.md" | awk -v v="## [$version]" '
    index($0, v) == 1 { found = 1; next }
    found && /^## \[/ { exit }
    found { print }
')
[ -n "$(tr -d '[:space:]' <<<"$notes")" ] || fail "no CHANGELOG.md section for $version at $merge_sha"

echo "PR #$pr_number merged as $merge_sha; releasing $tag"
run git tag -a "$tag" "$merge_sha" -m "$tag"
run git push origin "$tag"
run gh release create "$tag" --title "$tag" --notes "$notes"

# dev should fast-forward because the PR was merged with a merge commit.
if [ "$(git branch --show-current)" = "dev" ]; then
    run git merge --ff-only origin/main || fail "dev could not fast-forward to origin/main (was the PR squash-merged?)"
else
    echo "note: not on dev; skipped fast-forward of dev" >&2
fi

# Report whether the linked issues ended up closed.
gh pr view "$pr_number" --json closingIssuesReferences \
    --jq '.closingIssuesReferences[].number' | while read -r n; do
    state=$(gh issue view "$n" --json state --jq .state)
    echo "issue #$n: $state"
done

echo "finish OK: $tag"
