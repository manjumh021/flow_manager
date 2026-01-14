"""
Data models for Flow Manager system.
Defines the structure for Flow, Task, Condition, and execution state.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"


class FlowStatus(Enum):
    """Flow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """Represents a task in the flow"""
    name: str
    description: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description
        }


@dataclass
class Condition:
    """Represents a condition that evaluates task results"""
    name: str
    description: str
    source_task: str
    outcome: str  # "success" or "failure"
    target_task_success: str
    target_task_failure: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "source_task": self.source_task,
            "outcome": self.outcome,
            "target_task_success": self.target_task_success,
            "target_task_failure": self.target_task_failure
        }


@dataclass
class Flow:
    """Represents a complete flow definition"""
    id: str
    name: str
    start_task: str
    tasks: List[Task]
    conditions: List[Condition]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "start_task": self.start_task,
            "tasks": [task.to_dict() for task in self.tasks],
            "conditions": [condition.to_dict() for condition in self.conditions]
        }
    
    def get_task(self, task_name: str) -> Optional[Task]:
        """Get task by name"""
        for task in self.tasks:
            if task.name == task_name:
                return task
        return None
    
    def get_conditions_for_task(self, task_name: str) -> List[Condition]:
        """Get all conditions for a specific source task"""
        return [c for c in self.conditions if c.source_task == task_name]


@dataclass
class TaskExecutionResult:
    """Result of a task execution"""
    task_name: str
    status: TaskStatus
    data: Optional[Any] = None
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_name": self.task_name,
            "status": self.status.value,
            "data": self.data,
            "message": self.message,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class FlowExecutionState:
    """Tracks the state of a flow execution"""
    execution_id: str
    flow_id: str
    status: FlowStatus
    current_task: Optional[str] = None
    execution_history: List[TaskExecutionResult] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def add_task_result(self, result: TaskExecutionResult):
        """Add a task execution result to history"""
        self.execution_history.append(result)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "flow_id": self.flow_id,
            "status": self.status.value,
            "current_task": self.current_task,
            "execution_history": [r.to_dict() for r in self.execution_history],
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "error_message": self.error_message
        }
