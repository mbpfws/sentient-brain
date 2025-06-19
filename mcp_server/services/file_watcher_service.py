import time
import logging
import asyncio
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from sqlalchemy.orm import Session

from ..database import database
from . import code_indexing_service

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

class CodebaseChangeEventHandler(FileSystemEventHandler):
    """Handles file system events by calling the appropriate service function."""

    def __init__(self, project_alias: str):
        self.project_alias = project_alias
        super().__init__()

    def _get_db_session(self) -> Session:
        """Creates a new database session for the event handler."""
        db_session_gen = database.get_db()
        return next(db_session_gen)

    def _handle_event(self, service_call, event_name, event_path):
        db = self._get_db_session()
        try:
            logging.info(f"[Watcher] {event_name}: {event_path} in project '{self.project_alias}'. Triggering update.")
            # Run the async service call in a new event loop
            asyncio.run(service_call(db=db, project_alias=self.project_alias, file_path_str=event_path))
        except Exception as e:
            logging.error(f"[Watcher] Error processing {event_name} for {event_path}: {e}")
        finally:
            db.close()

    def on_created(self, event: FileSystemEvent):
        if not event.is_directory:
            self._handle_event(code_indexing_service.update_or_create_code_file_by_path, "Created", event.src_path)

    def on_modified(self, event: FileSystemEvent):
        if not event.is_directory:
            self._handle_event(code_indexing_service.update_or_create_code_file_by_path, "Modified", event.src_path)

    def on_deleted(self, event: FileSystemEvent):
        if not event.is_directory:
            db = self._get_db_session()
            try:
                logging.info(f"[Watcher] Deleted: {event.src_path} in project '{self.project_alias}'. Triggering update.")
                # This service function is synchronous
                code_indexing_service.delete_code_file_by_path(db=db, project_alias=self.project_alias, file_path_str=event.src_path)
            except Exception as e:
                logging.error(f"[Watcher] Error processing deletion for {event.src_path}: {e}")
            finally:
                db.close()


class WatcherService:
    """Manages multiple file system observers for all registered projects."""

    def __init__(self):
        self.observers = {}

    def watch_project(self, project):
        """Starts a new observer for a single project if not already watched."""
        if project.alias in self.observers:
            return

        path = Path(project.root_path)
        if path.is_dir():
            event_handler = CodebaseChangeEventHandler(project_alias=project.alias)
            observer = Observer()
            observer.schedule(event_handler, str(path), recursive=True)
            observer.start()
            self.observers[project.alias] = observer
            logging.info(f"[Watcher] Started monitoring project '{project.alias}' at {project.root_path}")
        else:
            logging.warning(f"[Watcher] Project '{project.alias}' root path not found or not a directory: {project.root_path}")

    def start(self):
        db_session_gen = database.get_db()
        db = next(db_session_gen)
        try:
            projects = code_indexing_service.get_projects(db)
            for project in projects:
                self.watch_project(project)
        finally:
            db.close()

    def stop(self):
        for alias, observer in self.observers.items():
            observer.stop()
            logging.info(f"[Watcher] Stopped monitoring project '{alias}'.")
        for observer in self.observers.values():
            observer.join()
        self.observers.clear()
        logging.info("[Watcher] All observer threads joined.")


# Global instance of the watcher service
file_watcher_service = WatcherService()
