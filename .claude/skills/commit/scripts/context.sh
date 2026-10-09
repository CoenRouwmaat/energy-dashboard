#!/usr/bin/env bash
# Snapshot of the working tree for the commit skill. Read-only: never touches the index.
#
# Output (stdout), in order:
#   BRANCH <name>
#   STAGED <path>       already staged before the skill ran (one line per path)
#   SENSITIVE <path>    changed or untracked path that looks like a secret; never stage it
#   == STATUS ==        git status --short
#   == DIFF ==          tracked changes vs HEAD (staged + unstaged); uv.lock as a stat only
#   == UNTRACKED ==     new files rendered as diffs, each capped at 200 lines
#   == RECENT ==        last 10 commits
# Exit 0 = changes to commit, 1 = abort (reason on stderr), 2 = working tree clean.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

# Print at most $1 lines of stdin, reading all of it (head would SIGPIPE the writer under pipefail).
cap() {
    awk -v n="$1" 'NR <= n { print } END { if (NR > n) print "... truncated (" NR - n " more lines)" }'
}

branch=$(git branch --show-current)
[ -n "$branch" ] || { echo "commit: detached HEAD; check out a branch first" >&2; exit 1; }
[ "$branch" != main ] || { echo "commit: on 'main'; work goes on 'dev' or a feature branch" >&2; exit 1; }

if [ -z "$(git status --porcelain)" ]; then
    echo "working tree clean"
    exit 2
fi

echo "BRANCH $branch"
git diff --cached --name-only | sed 's/^/STAGED /'
{ git status --porcelain | cut -c4- | grep -E '(^|/)(\.env($|\.)|id_rsa|credentials)|\.(pem|key|p12)$' || true; } | sed 's/^/SENSITIVE /'

echo "== STATUS =="
git status --short

echo "== DIFF =="
git diff HEAD --stat
git diff HEAD --no-color -- . ':(exclude)uv.lock' | cap 2000

echo "== UNTRACKED =="
git ls-files --others --exclude-standard -z | while IFS= read -r -d '' f; do
    git diff --no-index --no-color -- /dev/null "$f" | cap 200 || true
done

echo "== RECENT =="
git log --oneline -10
