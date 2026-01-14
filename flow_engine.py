"""
Core Flow Engine for managing flow execution.
Includes FlowParser, ConditionEvaluator, and FlowOrchestrator.
"""

import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from models import (
    Flow, Task, Condition, FlowExecutionState, TaskExecutionResult,
    FlowStatus, TaskStatus
)
from task_executor import task_registry

logger = logging.getLogger(__name__)


class FlowParser:
    """Parses JSON flow definitions into Flow objects"""
    
    @staticmethod
    def parse(flow_json: Dict[str, Any]) -> Flow:
        """
        Parse a JSON flow definition into a Flow object.
        
        Args:
            flow_json: Dictionary containing flow definition
            
        Returns:
            Flow object
            
        Raises:
            ValueError: If flow JSON is invalid
        """
        try:
            flow_data = flow_json.get("flow", flow_json)
            
            # Extract required fields
            flow_id = flow_data.get("id")
            name = flow_data.get("name")
            start_task = flow_data.get("start_task")
            
            if not all([flow_id, name, start_task]):
                raise ValueError("Flow must have 'id', 'name', and 'start_task'")
            
            # Parse tasks
            tasks_data = flow_data.get("tasks", [])
            tasks = [
                Task(
                    name=task["name"],
                    description=task.get("description", "")
                )
                for task in tasks_data
            ]
            
            if not tasks:
                raise ValueError("Flow must have at least one task")
            
            # Parse conditions
            conditions_data = flow_data.get("conditions", [])
            conditions = [
                Condition(
                    name=cond["name"],
                    description=cond.get("description", ""),
                    source_task=cond["source_task"],
                    outcome=cond.get("outcome", "success"),
                    target_task_success=cond["target_task_success"],
                    target_task_failure=cond["target_task_failure"]
                )
                for cond in conditions_data
            ]
            
            flow = Flow(
                id=flow_id,
                name=name,
                start_task=start_task,
                tasks=tasks,
                conditions=conditions
            )
            
            # Validate flow
            FlowParser.validate_flow(flow)
            
            return flow
            
        except KeyError as e:
            raise ValueError(f"Missing required field: {e}")
        except Exception as e:
            raise ValueError(f"Invalid flow definition: {str(e)}")
    
    @staticmethod
    def validate_flow(flow: Flow):
        """
        Validate that the flow is properly structured.
        
        Args:
            flow: Flow object to validate
            
        Raises:
            ValueError: If flow is invalid
        """
        task_names = {task.name for task in flow.tasks}
        
        # Check start_task exists
        if flow.start_task not in task_names:
            raise ValueError(f"start_task '{flow.start_task}' not found in tasks")
        
        # Check all conditions reference valid tasks
        for condition in flow.conditions:
            if condition.source_task not in task_names:
                raise ValueError(
                    f"Condition '{condition.name}' references unknown source_task '{condition.source_task}'"
                )
            
            if condition.target_task_success != "end" and condition.target_task_success not in task_names:
                raise ValueError(
                    f"Condition '{condition.name}' references unknown target_task_success '{condition.target_task_success}'"
                )
            
            if condition.target_task_failure != "end" and condition.target_task_failure not in task_names:
                raise ValueError(
                    f"Condition '{condition.name}' references unknown target_task_failure '{condition.target_task_failure}'"
                )


class ConditionEvaluator:
    """Evaluates conditions based on task results"""
    
    @staticmethod
    def evaluate(
        task_result: TaskExecutionResult,
        conditions: list[Condition]
    ) -> Optional[str]:
        """
        Evaluate conditions for a task result and return the next task.
        
        Args:
            task_result: Result of the task execution
            conditions: List of conditions to evaluate
            
        Returns:
            Name of the next task to execute, or "end" to end the flow
        """
        # Find conditions for this task
        task_conditions = [
            c for c in conditions 
            if c.source_task == task_result.task_name
        ]
        
        if not task_conditions:
            logger.warning(f"No conditions found for task '{task_result.task_name}', ending flow")
            return "end"
        
        # Evaluate based on task status
        for condition in task_conditions:
            if task_result.status == TaskStatus.SUCCESS and condition.outcome == "success":
                next_task = condition.target_task_success
                logger.info(
                    f"Condition '{condition.name}' matched (success): next task = '{next_task}'"
                )
                return next_task
            
            elif task_result.status == TaskStatus.FAILURE and condition.outcome == "failure":
                next_task = condition.target_task_failure
                logger.info(
                    f"Condition '{condition.name}' matched (failure): next task = '{next_task}'"
                )
                return next_task
        
        # If task succeeded but condition expects success, route to success target
        for condition in task_conditions:
            if condition.outcome == "success":
                if task_result.status == TaskStatus.SUCCESS:
                    return condition.target_task_success
                else:
                    return condition.target_task_failure
        
        # Default to end if no conditions match
        logger.warning(f"No matching condition for task '{task_result.task_name}', ending flow")
        return "end"


class FlowOrchestrator:
    """Orchestrates the execution of a flow"""
    
    def __init__(self):
        self.executions: Dict[str, FlowExecutionState] = {}
    
    def execute_flow(self, flow: Flow) -> FlowExecutionState:
        """
        Execute a complete flow.
        
        Args:
            flow: Flow object to execute
            
        Returns:
            FlowExecutionState with execution results
        """
        # Create execution state
        execution_id = str(uuid.uuid4())
        state = FlowExecutionState(
            execution_id=execution_id,
            flow_id=flow.id,
            status=FlowStatus.RUNNING,
            current_task=flow.start_task
        )
        
        self.executions[execution_id] = state
        
        logger.info(f"Starting flow execution: {execution_id} for flow: {flow.name}")
        
        try:
            current_task_name = flow.start_task
            
            while current_task_name != "end":
                # Update current task
                state.current_task = current_task_name
                
                # Get task definition
                task = flow.get_task(current_task_name)
                if not task:
                    raise ValueError(f"Task '{current_task_name}' not found in flow")
                
                # Execute task
                logger.info(f"Executing task: {current_task_name}")
                task_result = self._execute_task(current_task_name, state)
                
                # Add result to execution history
                state.add_task_result(task_result)
                
                # Evaluate conditions to determine next task
                next_task_name = ConditionEvaluator.evaluate(
                    task_result,
                    flow.conditions
                )
                
                logger.info(f"Next task: {next_task_name}")
                
                # If task failed and next is end, mark flow as failed
                if task_result.status == TaskStatus.FAILURE and next_task_name == "end":
                    state.status = FlowStatus.FAILED
                    state.error_message = task_result.message
                    break
                
                current_task_name = next_task_name
            
            # Flow completed successfully if we reached end without failure
            if state.status == FlowStatus.RUNNING:
                state.status = FlowStatus.COMPLETED
            
            state.end_time = datetime.now()
            logger.info(f"Flow execution completed: {execution_id} with status: {state.status.value}")
            
        except Exception as e:
            logger.error(f"Error during flow execution: {str(e)}")
            state.status = FlowStatus.FAILED
            state.error_message = str(e)
            state.end_time = datetime.now()
        
        return state
    
    def _execute_task(
        self,
        task_name: str,
        state: FlowExecutionState
    ) -> TaskExecutionResult:
        """
        Execute a single task.
        
        Args:
            task_name: Name of the task to execute
            state: Current flow execution state
            
        Returns:
            TaskExecutionResult
        """
        try:
            # Get task executor from registry
            executor = task_registry.get_executor(task_name)
            
            # Prepare context for task
            context = {
                "execution_id": state.execution_id,
                "flow_id": state.flow_id,
                "execution_history": state.execution_history
            }
            
            # Execute task
            result = executor.execute(context)
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing task '{task_name}': {str(e)}")
            return TaskExecutionResult(
                task_name=task_name,
                status=TaskStatus.FAILURE,
                message=f"Task execution error: {str(e)}",
                data=None
            )
    
    def get_execution_state(self, execution_id: str) -> Optional[FlowExecutionState]:
        """Get the state of a flow execution"""
        return self.executions.get(execution_id)
