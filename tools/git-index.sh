#!/usr/bin/env bash
# git-index.sh -- Git hook helper to feed changed files to Sentient Brain container
# Usage (inside repo):
#   tools/git-index.sh HEAD~1 # Process changes from the last commit
# Or install as a post-commit hook:
#   ln -s ../../tools/git-index.sh .git/hooks/post-commit

set -euo pipefail

# Get commit info
COMMIT_HASH=$(git rev-parse HEAD)
COMMIT_AUTHOR=$(git log -1 --pretty=format:'%an')

CONTAINER=${CONTAINER:-sentient-brain-py-server-server-1}
PROCESS_CLI="python -m src.cli.process_file"

# Get changed files from the specified commit (or HEAD~1 by default)
COMMIT_REF=${1:-HEAD~1}

FILES_CHANGED=$(git diff-tree --no-commit-id --name-only -r "$COMMIT_REF" HEAD | grep -E '\.(py|ts|js|yml|md)$' || true)

if [ -z "$FILES_CHANGED" ]; then
    echo "[GIT-INDEX] No relevant files changed in last commit."
    exit 0
fi

echo "[GIT-INDEX] Processing files changed in commit $COMMIT_HASH..."

for file in $FILES_CHANGED; do
    if [[ -f "$file" ]]; then
        echo "[GIT-INDEX] Processing $file"
        docker exec "$CONTAINER" $PROCESS_CLI --file "$file" --commit-hash "$COMMIT_HASH" --commit-author "$COMMIT_AUTHOR" || true
    fi
done

echo "[GIT-INDEX] Done."
