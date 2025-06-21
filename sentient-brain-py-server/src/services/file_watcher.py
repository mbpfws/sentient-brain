"""Service to watch for file system changes and trigger re-indexing.

Uses the `watchdog` library to monitor specified directories for modifications,
creations, or deletions, and then triggers the appropriate services to update
the knowledge graph and vector database.
"""
import asyncio
import os
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .code_graph_service import CodeGraphService


class CodeChangeHandler(FileSystemEventHandler):
    """Handles file system events for Python source files."""

    def __init__(self, code_graph_service: CodeGraphService):
        self.code_graph_service = code_graph_service
        print("Initialized CodeChangeHandler.")

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(".py"):
            print(f"Modified: {event.src_path}")
            self._process_file(event.src_path)

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".py"):
            print(f"Created: {event.src_path}")
            self._process_file(event.src_path)

    def _process_file(self, file_path: str):
        """Reads a file and triggers the graph processing service."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source_code = f.read()
            # Run the synchronous processing in a separate thread
            asyncio.to_thread(self.code_graph_service.process_file, file_path, source_code)
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")


class FileWatcherService:
    """Manages the file system observer."""

    def __init__(self, paths_to_watch: list[str], code_graph_service: CodeGraphService):
        self.observer = Observer()
        self.paths_to_watch = paths_to_watch
        self.code_graph_service = code_graph_service

    def start(self):
        """Starts the file watcher in a background thread."""
        event_handler = CodeChangeHandler(self.code_graph_service)
        for path in self.paths_to_watch:
            if Path(path).exists():
                self.observer.schedule(event_handler, path, recursive=True)
                print(f"Watching for changes in: {path}")
            else:
                print(f"Warning: Watch path does not exist, skipping: {path}")
        
        self.observer.start()
        print("File watcher started.")

    def stop(self):
        """Stops the file watcher."""
        self.observer.stop()
        self.observer.join()
        print("File watcher stopped.")
