"""
CLI entrypoint to process a single file and add it to the knowledge graph.
"""

import os
import sys
import argparse

# Add the project root to Python path to resolve relative imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

try:
    from src.services.code_graph_service import CodeGraphService
except ImportError:
    # Fallback for when running as module
    from services.code_graph_service import CodeGraphService

def main():
    parser = argparse.ArgumentParser(description="Process a source code file for the knowledge graph.")
    parser.add_argument("--file", required=True, help="The absolute path to the file to process.")
    parser.add_argument("--commit-hash", help="The Git commit hash.")
    parser.add_argument("--commit-author", help="The Git commit author.")
    args = parser.parse_args()

    file_path = args.file
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        sys.exit(1)

    with open(file_path, 'r', encoding='utf-8') as f:
        source_code = f.read()

    try:
        # Initialize the service and process the file
        service = CodeGraphService()
        service.process_file(
            file_path=file_path, 
            source_code=source_code,
            commit_hash=args.commit_hash,
            commit_author=args.commit_author
        )
        print(f"✓ Successfully processed {file_path}")
        if args.commit_hash:
            print(f"✓ Linked to commit {args.commit_hash}")
    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
