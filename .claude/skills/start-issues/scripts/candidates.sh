#!/usr/bin/env bash
# List open issues on the "Energy dashboard" project that are candidates to start.
#
# Output (stdout), tab-separated, one line each:
#   IN_PROGRESS  #N  [labels]  title     already being worked on (context only, never a candidate)
#   CANDIDATE    #N  [labels]  title     status Todo (or no status), issue open
# Exit 0 = OK, 1 = gh failed.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

PROJECT_NUMBER="${PROJECT_NUMBER:-2}" # "Energy dashboard" GitHub project

gh project item-list "$PROJECT_NUMBER" --owner @me --limit 200 --format json |
    python3 -I -c '
import json, sys
for it in sorted(json.load(sys.stdin)["items"], key=lambda i: i.get("content", {}).get("number", 0)):
    c = it.get("content", {})
    if c.get("type") != "Issue":
        continue
    status = it.get("status", "")
    if status == "Done":
        continue
    kind = "IN_PROGRESS" if status == "In Progress" else "CANDIDATE"
    labels = ",".join(it.get("labels", []))
    print("\t".join([kind, "#" + str(c["number"]), "[" + labels + "]", c["title"]]))
'
