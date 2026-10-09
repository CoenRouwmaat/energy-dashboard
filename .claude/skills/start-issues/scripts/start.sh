#!/usr/bin/env bash
# Move issues to "In Progress" on the "Energy dashboard" project.
#
# Usage: start.sh N [N...]
# Output: one line per issue, "STARTED #N title".
# Exit 0 = all moved, 1 = an issue is not on the project, closed, or gh failed (nothing is rolled back).
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

PROJECT_NUMBER="${PROJECT_NUMBER:-2}" # "Energy dashboard" GitHub project
[ $# -ge 1 ] || { echo "usage: start.sh N [N...]" >&2; exit 1; }

owner=$(gh repo view --json owner --jq .owner.login)
project_id=$(gh project view "$PROJECT_NUMBER" --owner "$owner" --format json --jq .id)
read -r field_id option_id < <(
    gh project field-list "$PROJECT_NUMBER" --owner "$owner" --format json |
        python3 -I -c '
import json, sys
f = next(f for f in json.load(sys.stdin)["fields"] if f["name"] == "Status")
o = next(o for o in f["options"] if o["name"] == "In Progress")
print(f["id"], o["id"])
'
)
items=$(gh project item-list "$PROJECT_NUMBER" --owner "$owner" --limit 200 --format json)

for n in "$@"; do
    n=${n#\#}
    row=$(printf '%s' "$items" | python3 -I -c '
import json, sys
n = int(sys.argv[1])
for it in json.load(sys.stdin)["items"]:
    c = it.get("content", {})
    if c.get("type") == "Issue" and c.get("number") == n:
        print(it["id"], it.get("status", ""), it["title"], sep="\t")
        break
' "$n")
    [ -n "$row" ] || { echo "issue #$n is not on project $PROJECT_NUMBER" >&2; exit 1; }
    IFS=$'\t' read -r item_id status title <<<"$row"
    [ "$(gh issue view "$n" --json state --jq .state)" = OPEN ] || { echo "issue #$n is closed" >&2; exit 1; }
    gh project item-edit --id "$item_id" --project-id "$project_id" \
        --field-id "$field_id" --single-select-option-id "$option_id" >/dev/null
    echo "STARTED #$n $title"
done
