"""
Sample task implementations for demonstration.
These tasks simulate the example flow: Fetch -> Process -> Store data.
"""

import time
import random
from typing import Dict, Any
from task_executor import TaskExecutor, register_task
from models import TaskExecutionResult, TaskStatus
import logging

logger = logging.getLogger(__name__)


@register_task("task1")
class FetchDataTask(TaskExecutor):
    """Task 1: Fetch data from a simulated data source"""
    
    def execute(self, context: Dict[str, Any]) -> TaskExecutionResult:
        logger.info("Executing FetchDataTask...")
        
        try:
            # Simulate fetching data with some delay
            time.sleep(0.5)
            
            # Simulate occasional failures (10% chance)
            if random.random() < 0.1:
                return TaskExecutionResult(
                    task_name="task1",
                    status=TaskStatus.FAILURE,
                    message="Failed to fetch data: Connection timeout",
                    data=None
                )
            
            # Successful fetch
            fetched_data = {
                "records": [
                    {"id": 1, "value": 100},
                    {"id": 2, "value": 200},
                    {"id": 3, "value": 300}
                ],
                "count": 3,
                "source": "sample_database"
            }
            
            logger.info(f"Successfully fetched {fetched_data['count']} records")
            
            return TaskExecutionResult(
                task_name="task1",
                status=TaskStatus.SUCCESS,
                message="Data fetched successfully",
                data=fetched_data
            )
            
        except Exception as e:
            logger.error(f"Error in FetchDataTask: {str(e)}")
            return TaskExecutionResult(
                task_name="task1",
                status=TaskStatus.FAILURE,
                message=f"Error: {str(e)}",
                data=None
            )


@register_task("task2")
class ProcessDataTask(TaskExecutor):
    """Task 2: Process the fetched data"""
    
    def execute(self, context: Dict[str, Any]) -> TaskExecutionResult:
        logger.info("Executing ProcessDataTask...")
        
        try:
            # Get data from previous task (task1)
            previous_results = context.get("execution_history", [])
            task1_result = None
            
            for result in previous_results:
                if result.task_name == "task1":
                    task1_result = result
                    break
            
            if not task1_result or task1_result.status != TaskStatus.SUCCESS:
                return TaskExecutionResult(
                    task_name="task2",
                    status=TaskStatus.FAILURE,
                    message="No data from task1 to process",
                    data=None
                )
            
            # Process the data
            time.sleep(0.5)
            
            raw_data = task1_result.data
            records = raw_data.get("records", [])
            
            # Apply some transformation (e.g., calculate sum and average)
            total_value = sum(record["value"] for record in records)
            avg_value = total_value / len(records) if records else 0
            
            processed_data = {
                "original_count": len(records),
                "total_value": total_value,
                "average_value": avg_value,
                "processed_records": [
                    {**record, "normalized": record["value"] / total_value}
                    for record in records
                ]
            }
            
            logger.info(f"Processed {len(records)} records, total: {total_value}, avg: {avg_value}")
            
            return TaskExecutionResult(
                task_name="task2",
                status=TaskStatus.SUCCESS,
                message="Data processed successfully",
                data=processed_data
            )
            
        except Exception as e:
            logger.error(f"Error in ProcessDataTask: {str(e)}")
            return TaskExecutionResult(
                task_name="task2",
                status=TaskStatus.FAILURE,
                message=f"Error: {str(e)}",
                data=None
            )


@register_task("task3")
class StoreDataTask(TaskExecutor):
    """Task 3: Store the processed data"""
    
    def execute(self, context: Dict[str, Any]) -> TaskExecutionResult:
        logger.info("Executing StoreDataTask...")
        
        try:
            # Get data from previous task (task2)
            previous_results = context.get("execution_history", [])
            task2_result = None
            
            for result in previous_results:
                if result.task_name == "task2":
                    task2_result = result
                    break
            
            if not task2_result or task2_result.status != TaskStatus.SUCCESS:
                return TaskExecutionResult(
                    task_name="task3",
                    status=TaskStatus.FAILURE,
                    message="No processed data from task2 to store",
                    data=None
                )
            
            # Simulate storing data
            time.sleep(0.5)
            
            processed_data = task2_result.data
            
            # In a real system, this would write to a database
            storage_result = {
                "stored": True,
                "location": "sample_storage/processed_data.json",
                "record_count": processed_data.get("original_count", 0),
                "storage_id": f"STORE_{int(time.time())}"
            }
            
            logger.info(f"Data stored successfully at {storage_result['location']}")
            
            return TaskExecutionResult(
                task_name="task3",
                status=TaskStatus.SUCCESS,
                message="Data stored successfully",
                data=storage_result
            )
            
        except Exception as e:
            logger.error(f"Error in StoreDataTask: {str(e)}")
            return TaskExecutionResult(
                task_name="task3",
                status=TaskStatus.FAILURE,
                message=f"Error: {str(e)}",
                data=None
            )
