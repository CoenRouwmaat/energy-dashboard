#!/usr/bin/env bash
# PreToolUse hook for the commit skill. Reads the tool call as JSON on stdin and blocks
# (exit 2, message on stderr) Bash commands the skill promises never to run directly.
# The skill's own scripts may do these things internally; only the command Claude issues is checked.
set -euo pipefail

command=$(jq -r '.tool_input.command // empty')
[ -n "$command" ] || exit 0

block() {
    echo "commit guard: blocked. $1" >&2
    exit 2
}

# A loose regex is fine: a false positive just asks for a manual step.
git_cmd='(^|[;&|[:space:]])git[[:space:]]+'

if grep -qE "${git_cmd}commit\b.*(--no-verify|[[:space:]]-[a-zA-Z]*n[a-zA-Z]*([[:space:]]|$))" <<<"$command"; then
    block "Hooks must not be skipped (--no-verify / -n)."
fi
if grep -qE "${git_cmd}commit\b.*(--amend|--all|[[:space:]]-[a-zA-Z]*a[a-zA-Z]*([[:space:]]|$))" <<<"$command"; then
    block "No --amend and no -a/--all; stage explicit paths and make a new commit."
fi
if grep -qE "${git_cmd}add\b.*[[:space:]](-A|--all|-u|--update|-f|--force|\.|\*)([[:space:]]|$)" <<<"$command"; then
    block "Stage explicit paths only (no -A, -u, -f, '.' or '*')."
fi
if grep -qE "${git_cmd}push\b" <<<"$command"; then
    block "Pushing is not part of this skill."
fi
if grep -qE "${git_cmd}(reset[[:space:]]+--hard|clean\b)" <<<"$command"; then
    block "Destructive commands are not allowed."
fi
if grep -qE "${git_cmd}restore\b" <<<"$command" && ! grep -qE -- '--staged' <<<"$command"; then
    block "git restore may only unstage (--staged), never discard working-tree changes."
fi

exit 0
