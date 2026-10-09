#!/usr/bin/env bash
# List issues referenced by Closes/Fixes/Resolves #N in commits since the last tag.
#
# Output (stdout), one line each:
#   CLOSES #N <state> <title>            referenced issue; state is OPEN or CLOSED
#   UNREFERENCED #N <title>              "In Progress" on the project but no commit references it (warning only)
# Exit 0 = every referenced issue exists; exit 1 = a referenced issue does not exist (details on stderr).
# Already-closed issues are reported with state CLOSED but do not fail the script.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

PROJECT_NUMBER="${PROJECT_NUMBER:-2}" # "Energy dashboard" GitHub project

last_tag=$(git describe --tags --abbrev=0 2>/dev/null || true)
range="${last_tag:+$last_tag..}HEAD"

refs=$(git log --format=%B "$range" |
    grep -ioE '\b(close[sd]?|fix(e[sd])?|resolve[sd]?)[: ]+#[0-9]+' |
    grep -oE '[0-9]+' | sort -un || true)

status=0
for n in $refs; do
    if info=$(gh issue view "$n" --json state,title --jq '"\(.state) \(.title)"' 2>/dev/null); then
        echo "CLOSES #$n $info"
    else
        echo "issue #$n is referenced but does not exist" >&2
        status=1
    fi
done

# Warn about In Progress items that no commit references.
in_progress=$(gh project item-list "$PROJECT_NUMBER" --owner @me --limit 200 --format json \
    --jq '.items[] | select(.status=="In Progress" and .content.type=="Issue") | "\(.content.number) \(.title)"' \
    2>/dev/null || true)
while IFS= read -r line; do
    [ -n "$line" ] || continue
    n=${line%% *}
    if ! grep -qx "$n" <<<"$refs"; then
        echo "UNREFERENCED #$n ${line#* }"
    fi
done <<<"$in_progress"

exit "$status"
