"""Service to watch for file system changes and trigger re-indexing.

Uses the `watchdog` library to monitor specified directories for modifications,
creations, or deletions, and then triggers the appropriate services to update
the knowledge graph and vector database.
"""
import asyncio
import threading
import os
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers.polling import PollingObserver

from .code_graph_service import CodeGraphService
from ..parsers.registry import get_parser_registry


class CodeChangeHandler(FileSystemEventHandler):
    """Handles file system events for Python source files."""

    def __init__(self, code_graph_service: CodeGraphService):
        self.code_graph_service = code_graph_service
        print("Initialized CodeChangeHandler with comprehensive event logging.")

    def on_any_event(self, event):
        """Log ALL events for debugging purposes."""
        event_type = event.event_type
        src_path = event.src_path
        is_directory = event.is_directory
        
        print(f"[FILE_WATCHER] Event detected: {event_type} | Path: {src_path} | Is Dir: {is_directory}", flush=True)
        
        # Also log the file extension if it's a file
        if not is_directory:
            ext = Path(src_path).suffix
            print(f"[FILE_WATCHER] File extension: {ext}", flush=True)

    def on_modified(self, event):
        print(f"[FILE_WATCHER] on_modified triggered: {event.src_path}", flush=True)
        if event.is_directory:
            print(f"[FILE_WATCHER] Skipping directory: {event.src_path}", flush=True)
            return
        
        ext = Path(event.src_path).suffix
        parser = get_parser_registry().get_parser_for_ext(ext)
        
        if parser:
            print(f"[FILE_WATCHER] Parser found for {ext}: Processing {event.src_path}", flush=True)
            self._process_file(event.src_path)
        else:
            print(f"[FILE_WATCHER] No parser for extension {ext}, skipping {event.src_path}", flush=True)

    def on_created(self, event):
        print(f"[FILE_WATCHER] on_created triggered: {event.src_path}", flush=True)
        if event.is_directory:
            print(f"[FILE_WATCHER] Skipping directory creation: {event.src_path}", flush=True)
            return
        
        ext = Path(event.src_path).suffix
        parser = get_parser_registry().get_parser_for_ext(ext)
        
        if parser:
            print(f"[FILE_WATCHER] Parser found for {ext}: Processing new file {event.src_path}", flush=True)
            self._process_file(event.src_path)
        else:
            print(f"[FILE_WATCHER] No parser for extension {ext}, skipping new file {event.src_path}", flush=True)

    def on_moved(self, event):
        print(f"[FILE_WATCHER] on_moved triggered: {event.src_path} -> {event.dest_path}", flush=True)
        # Handle moved files as a delete + create
        if not event.is_directory:
            ext = Path(event.dest_path).suffix
            if get_parser_registry().get_parser_for_ext(ext):
                print(f"[FILE_WATCHER] Processing moved file: {event.dest_path}", flush=True)
                self._process_file(event.dest_path)

    def on_deleted(self, event):
        print(f"[FILE_WATCHER] on_deleted triggered: {event.src_path}", flush=True)
        # For deletions, we might want to remove from Neo4j/Weaviate in the future
        # For now, just log it
        if not event.is_directory:
            ext = Path(event.src_path).suffix
            if get_parser_registry().get_parser_for_ext(ext):
                print(f"[FILE_WATCHER] Code file deleted: {event.src_path} (cleanup not implemented yet)", flush=True)

    def _process_file(self, file_path: str):
        """Reads a file and triggers the graph processing service."""
        try:
            print(f"[FILE_WATCHER] Reading file: {file_path}", flush=True)
            
            # Check if file exists (might have been deleted between event and processing)
            if not os.path.exists(file_path):
                print(f"[FILE_WATCHER] File no longer exists: {file_path}", flush=True)
                return
                
            with open(file_path, "r", encoding="utf-8") as f:
                source_code = f.read()

            print(f"[FILE_WATCHER] File read successfully, content length: {len(source_code)} chars", flush=True)

            # Offload heavy processing to a background thread (watchdog callbacks are sync)
            thread = threading.Thread(
                target=self._process_file_background,
                args=(file_path, source_code),
                daemon=True,
            )
            thread.start()
            print(f"[FILE_WATCHER] Background processing thread started for: {file_path}", flush=True)
            
        except Exception as e:
            print(f"[FILE_WATCHER] Error processing file {file_path}: {e}", flush=True)

    def _process_file_background(self, file_path: str, source_code: str):
        """Background thread processing to avoid blocking the file watcher."""
        try:
            print(f"[FILE_WATCHER] Background processing started for: {file_path}", flush=True)
            self.code_graph_service.process_file(file_path, source_code)
            print(f"[FILE_WATCHER] Background processing completed for: {file_path}", flush=True)
        except Exception as e:
            print(f"[FILE_WATCHER] Error in background processing for {file_path}: {e}", flush=True)


class FileWatcherService:
    """Manages the file system observer with aggressive polling for Docker environments."""

    def __init__(self, paths_to_watch: list[str], code_graph_service: CodeGraphService):
        # Use more aggressive polling for Docker environments
        self.observer = PollingObserver(timeout=0.5)  # Poll every 500ms instead of default 1s
        self.paths_to_watch = paths_to_watch
        self.code_graph_service = code_graph_service
        print(f"[FILE_WATCHER] Initialized with aggressive polling (500ms interval)", flush=True)

    def start(self):
        """Starts the file watcher in a background thread."""
        event_handler = CodeChangeHandler(self.code_graph_service)
        
        for path in self.paths_to_watch:
            # Convert to absolute path for better reliability
            abs_path = os.path.abspath(path)
            
            print(f"[FILE_WATCHER] Checking path: {path} -> {abs_path}", flush=True)
            
            if Path(abs_path).exists():
                self.observer.schedule(event_handler, abs_path, recursive=True)
                print(f"[FILE_WATCHER] Successfully watching: {abs_path}", flush=True)
                
                # List some files in the directory for verification
                try:
                    files = list(Path(abs_path).rglob("*.py"))[:5]  # First 5 Python files
                    print(f"[FILE_WATCHER] Sample Python files in {abs_path}: {[str(f) for f in files]}", flush=True)
                except Exception as e:
                    print(f"[FILE_WATCHER] Could not list files in {abs_path}: {e}", flush=True)
            else:
                print(f"[FILE_WATCHER] ERROR: Watch path does not exist: {abs_path}", flush=True)
        
        self.observer.start()
        print(f"[FILE_WATCHER] Observer started with PID: {os.getpid()}", flush=True)
        print(f"[FILE_WATCHER] Observer is alive: {self.observer.is_alive()}", flush=True)

    def stop(self):
        """Stops the file watcher."""
        print("[FILE_WATCHER] Stopping file watcher...", flush=True)
        self.observer.stop()
        self.observer.join()
        print("[FILE_WATCHER] File watcher stopped.", flush=True)
