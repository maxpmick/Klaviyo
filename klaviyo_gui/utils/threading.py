"""
Threading utilities for background task management
"""

import threading
import logging
from typing import Callable, Any, Optional
from queue import Queue, Empty
import time


class BackgroundTask:
    """
    Manages a background task with progress updates and cancellation
    """
    
    def __init__(self, target: Callable, args: tuple = (), kwargs: dict = None):
        self.target = target
        self.args = args
        self.kwargs = kwargs or {}
        self.thread = None
        self.result = None
        self.error = None
        self.is_running = False
        self.is_cancelled = False
        self.progress_queue = Queue()
        self.logger = logging.getLogger(__name__)
    
    def start(self):
        """Start the background task"""
        if self.is_running:
            raise RuntimeError("Task is already running")
        
        self.is_running = True
        self.is_cancelled = False
        self.result = None
        self.error = None
        
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        self.logger.info("Background task started")
    
    def _run(self):
        """Internal method to run the task"""
        try:
            # Add a should_stop function to kwargs if the target supports it
            if 'should_stop' in self.target.__code__.co_varnames:
                self.kwargs['should_stop'] = lambda: self.is_cancelled
            
            self.result = self.target(*self.args, **self.kwargs)
            self.logger.info("Background task completed successfully")
        except Exception as e:
            self.error = e
            self.logger.error(f"Background task failed: {e}")
        finally:
            self.is_running = False
    
    def cancel(self):
        """Cancel the background task"""
        self.is_cancelled = True
        self.logger.info("Background task cancellation requested")
    
    def is_alive(self) -> bool:
        """Check if the task is still running"""
        return self.thread and self.thread.is_alive()
    
    def join(self, timeout: Optional[float] = None):
        """Wait for the task to complete"""
        if self.thread:
            self.thread.join(timeout)
    
    def get_progress_updates(self) -> list:
        """Get all pending progress updates"""
        updates = []
        try:
            while True:
                update = self.progress_queue.get_nowait()
                updates.append(update)
        except Empty:
            pass
        return updates
    
    def add_progress_update(self, update: Any):
        """Add a progress update (called from the background thread)"""
        self.progress_queue.put(update)


class TaskManager:
    """
    Manages multiple background tasks
    """
    
    def __init__(self):
        self.tasks = {}
        self.logger = logging.getLogger(__name__)
    
    def start_task(self, task_id: str, target: Callable, args: tuple = (), kwargs: dict = None) -> BackgroundTask:
        """Start a new background task"""
        if task_id in self.tasks and self.tasks[task_id].is_alive():
            raise RuntimeError(f"Task {task_id} is already running")
        
        task = BackgroundTask(target, args, kwargs)
        self.tasks[task_id] = task
        task.start()
        return task
    
    def get_task(self, task_id: str) -> Optional[BackgroundTask]:
        """Get a task by ID"""
        return self.tasks.get(task_id)
    
    def cancel_task(self, task_id: str):
        """Cancel a task by ID"""
        task = self.tasks.get(task_id)
        if task:
            task.cancel()
    
    def cancel_all_tasks(self):
        """Cancel all running tasks"""
        for task in self.tasks.values():
            if task.is_alive():
                task.cancel()
    
    def cleanup_finished_tasks(self):
        """Remove finished tasks from the manager"""
        finished_tasks = [
            task_id for task_id, task in self.tasks.items()
            if not task.is_alive()
        ]
        for task_id in finished_tasks:
            del self.tasks[task_id]
    
    def get_running_tasks(self) -> list:
        """Get list of currently running task IDs"""
        return [
            task_id for task_id, task in self.tasks.items()
            if task.is_alive()
        ]


class ProgressReporter:
    """
    Helper class for reporting progress from background tasks
    """
    
    def __init__(self, task: BackgroundTask):
        self.task = task
    
    def report(self, message: str, progress: Optional[float] = None, data: Any = None):
        """Report progress with optional percentage and data"""
        update = {
            'message': message,
            'progress': progress,
            'data': data,
            'timestamp': time.time()
        }
        self.task.add_progress_update(update)


# Global task manager instance
task_manager = TaskManager()