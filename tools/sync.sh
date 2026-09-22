#!/usr/bin/env bash
# Synchronize the current branch; stop on any failed command.
set -euo pipefail
cd "$(dirname "$0")/.."
mode="${1:-start}"
case "$mode" in start|end) ;; *) echo 'Use start or end' >&2; exit 1;; esac
branch=$(git symbolic-ref --quiet --short HEAD)
if [ -n "$(git ls-files --unmerged)" ]; then echo 'Resolve merge conflicts first.' >&2; exit 1; fi
if [ -d "$(git rev-parse --git-path rebase-merge)" ] || [ -d "$(git rev-parse --git-path rebase-apply)" ]; then
  echo 'Finish the current rebase first.' >&2; exit 1
fi
if [ "$mode" = end ]; then
  msg="${2:-}"
  if [ -z "$msg" ]; then echo 'Provide a commit message.' >&2; exit 1; fi
  git add -A
  if git diff --cached --quiet; then :
  else
    status=$?
    if [ "$status" -ne 1 ]; then exit "$status"; fi
    git commit -m "$msg"
  fi
elif [ -n "$(git status --porcelain)" ]; then
  echo 'Working tree has changes. Commit or stash before start.' >&2; exit 1
fi
git fetch origin
if git show-ref --verify --quiet "refs/remotes/origin/$branch"; then
  if [ "$mode" = start ]; then git merge --ff-only "origin/$branch"; else git rebase "origin/$branch"; fi
else
  status=$?
  if [ "$status" -ne 1 ]; then exit "$status"; fi
fi
if [ "$mode" = end ]; then git push -u origin "HEAD:refs/heads/$branch"; fi
echo "Synchronized branch: $branch"
