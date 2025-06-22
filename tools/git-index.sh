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
    echo "[GIT-INDEX] No relevant files changed in commit $COMMIT_HASH."
    exit 0
fi

echo "[GIT-INDEX] Processing files changed in commit $COMMIT_HASH by $COMMIT_AUTHOR..."

# Convert host path to container path
# Host paths like "sentient-brain-py-server/src/helpers/dummy.py" become "/app/src/helpers/dummy.py"
convert_to_container_path() {
    local host_path="$1"
    # Remove leading ./ if present
    host_path="${host_path#./}"
    
    # If path starts with sentient-brain-py-server/src/, convert to /app/src/
    if [[ "$host_path" =~ ^sentient-brain-py-server/src/ ]]; then
        # Remove sentient-brain-py-server/ prefix and add /app/
        container_path="${host_path#sentient-brain-py-server/}"
        echo "/app/$container_path"
    # If path starts with src/, convert to /app/src/
    elif [[ "$host_path" =~ ^src/ ]]; then
        echo "/app/$host_path"
    else
        # For other paths, try to determine if they should be in /app
        echo "/app/$host_path"
    fi
}

for file in $FILES_CHANGED; do
    if [[ -f "$file" ]]; then
        container_path=$(convert_to_container_path "$file")
        echo "[GIT-INDEX] Processing $file -> $container_path"
        
        # Use MSYS_NO_PATHCONV to prevent Git Bash path conversion on Windows
        # Capture both stdout and stderr for better error reporting
        if MSYS_NO_PATHCONV=1 docker exec "$CONTAINER" $PROCESS_CLI --file "$container_path" --commit-hash "$COMMIT_HASH" --commit-author "$COMMIT_AUTHOR" 2>&1; then
            echo "[GIT-INDEX] ✓ Successfully processed $file"
        else
            echo "[GIT-INDEX] ✗ Failed to process $file (exit code: $?)"
        fi
    else
        echo "[GIT-INDEX] ⚠ File not found on host: $file (may have been deleted)"
    fi
done

echo "[GIT-INDEX] Done processing commit $COMMIT_HASH."
