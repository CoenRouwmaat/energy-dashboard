#!/usr/bin/env bash
# PreToolUse hook for the release skill. Reads the tool call as JSON on stdin and blocks
# (exit 2, message on stderr) Bash commands the skill promises never to run directly.
# The skill's own scripts may do these things internally; only the command Claude issues is checked.
set -euo pipefail

command=$(jq -r '.tool_input.command // empty')
[ -n "$command" ] || exit 0

block() {
    echo "release guard: blocked. $1" >&2
    exit 2
}

# Only look at git/gh invocations; a loose regex is fine, a false positive just asks for a manual step.
if grep -qE '(^|[;&|[:space:]])git[[:space:]]+(commit|push)\b.*(--no-verify|[[:space:]]-[a-zA-Z]*n[a-zA-Z]*([[:space:]]|$))' <<<"$command"; then
    block "Hooks must not be skipped (--no-verify / -n)."
fi
if grep -qE '(^|[;&|[:space:]])git[[:space:]]+push\b.*([[:space:]]--force|[[:space:]]-[a-zA-Z]*f[a-zA-Z]*([[:space:]]|$)|[[:space:]]\+[^[:space:]]+)' <<<"$command"; then
    block "Force-pushing is not allowed."
fi
if grep -qE '(^|[;&|[:space:]])git[[:space:]]+push\b.*([[:space:]]|:)main([[:space:]]|$)' <<<"$command"; then
    block "Never push to main directly; main changes through the release PR."
fi
if grep -qE '(^|[;&|[:space:]])git[[:space:]]+push\b' <<<"$command" && [ "$(git branch --show-current 2>/dev/null)" = "main" ]; then
    block "Currently on main; never push from main."
fi
if grep -qE '(^|[;&|[:space:]])git[[:space:]]+tag[[:space:]]+(-[adsf]|--delete|--annotate|--sign|--force|[^-[:space:]])' <<<"$command"; then
    block "Tags are created by scripts/finish.sh (/release finish), not by hand."
fi
if grep -qE '(^|[;&|[:space:]])gh[[:space:]]+(release[[:space:]]+create|pr[[:space:]]+merge)\b' <<<"$command"; then
    block "Releases are created by scripts/finish.sh, and the release PR is merged by the user."
fi

exit 0
