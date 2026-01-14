"""
Task Executor module for Flow Manager.
Provides base classes and registry for task implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Type
from models import TaskExecutionResult, TaskStatus
import logging

logger = logging.getLogger(__name__)


class TaskExecutor(ABC):
    """Abstract base class for all task executors"""
    
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> TaskExecutionResult:
        """
        Execute the task with given context.
        
        Args:
            context: Dictionary containing data from previous tasks and flow state
            
        Returns:
            TaskExecutionResult with status and data
        """
        pass
    
    def get_name(self) -> str:
        """Get the task name (defaults to class name without 'Task' suffix)"""
        class_name = self.__class__.__name__
        if class_name.endswith('Task'):
            return class_name[:-4].lower()
        return class_name.lower()


class TaskRegistry:
    """Registry for managing task executor implementations"""
    
    _instance = None
    _tasks: Dict[str, Type[TaskExecutor]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TaskRegistry, cls).__new__(cls)
            cls._instance._tasks = {}
        return cls._instance
    
    def register(self, task_name: str, task_class: Type[TaskExecutor]):
        """
        Register a task executor class.
        
        Args:
            task_name: Name to identify the task
            task_class: TaskExecutor subclass
        """
        if not issubclass(task_class, TaskExecutor):
            raise ValueError(f"{task_class} must inherit from TaskExecutor")
        
        self._tasks[task_name] = task_class
        logger.info(f"Registered task: {task_name}")
    
    def get_executor(self, task_name: str) -> TaskExecutor:
        """
        Get an instance of a task executor.
        
        Args:
            task_name: Name of the task
            
        Returns:
            Instance of the task executor
            
        Raises:
            KeyError: If task not found in registry
        """
        if task_name not in self._tasks:
            raise KeyError(f"Task '{task_name}' not found in registry. Available tasks: {list(self._tasks.keys())}")
        
        task_class = self._tasks[task_name]
        return task_class()
    
    def is_registered(self, task_name: str) -> bool:
        """Check if a task is registered"""
        return task_name in self._tasks
    
    def get_all_tasks(self) -> Dict[str, Type[TaskExecutor]]:
        """Get all registered tasks"""
        return self._tasks.copy()
    
    def clear(self):
        """Clear all registered tasks (mainly for testing)"""
        self._tasks.clear()


# Global registry instance
task_registry = TaskRegistry()


def register_task(task_name: str):
    """
    Decorator to register a task executor.
    
    Usage:
        @register_task("task1")
        class MyTask(TaskExecutor):
            def execute(self, context):
                ...
    """
    def decorator(task_class: Type[TaskExecutor]):
        task_registry.register(task_name, task_class)
        return task_class
    return decorator
