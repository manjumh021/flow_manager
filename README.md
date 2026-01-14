# Flow Manager Microservice

A generic Flow Manager system that executes tasks sequentially based on configurable conditions. Built with Python Flask as a RESTful microservice.

## Overview

The Flow Manager allows you to define workflows with tasks and conditions in JSON format. Tasks are executed sequentially, and conditions determine whether to proceed to the next task or end the flow based on success/failure outcomes.

## Features

- ✅ **Generic Flow Engine**: Support for any number of tasks and conditions
- ✅ **Sequential Execution**: Tasks execute one after another with conditional routing
- ✅ **REST API**: Full-featured API for flow execution and monitoring
- ✅ **Extensible**: Easy to add new task types via task registry
- ✅ **State Management**: Track execution history and status
- ✅ **Error Handling**: Robust error handling and logging

## Architecture

### Flow Design

**Task Dependencies:**
- Tasks are linked through conditions defined in the flow JSON
- Each condition evaluates a source task's result
- Based on success/failure, the flow routes to the next task or ends

**Success/Failure Evaluation:**
- Each task returns a `TaskExecutionResult` with status (SUCCESS/FAILURE)
- Conditions match the task result status against expected outcome
- Routing decision:
  - `target_task_success`: Next task if condition matched
  - `target_task_failure`: Where to go if condition fails (typically "end")

**Flow Lifecycle:**
1. Parse JSON flow definition
2. Start with `start_task`
3. Execute task → Get result
4. Evaluate conditions → Determine next task
5. Repeat until reaching "end"

### Components

```
├── app.py              # Flask REST API
├── flow_engine.py      # Core flow orchestration
│   ├── FlowParser      # Parse JSON to Flow objects
│   ├── ConditionEvaluator  # Evaluate conditions
│   └── FlowOrchestrator    # Execute flows
├── task_executor.py    # Task execution framework
│   ├── TaskExecutor    # Base class for tasks
│   └── TaskRegistry    # Task registration
├── sample_tasks.py     # Example task implementations
├── models.py           # Data models
└── sample_flow.json    # Example flow definition
```

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify installation:**
   ```bash
   python -c "import flask; print(flask.__version__)"
   ```

## Usage

### Start the Server

```bash
python app.py
```

The server will start on `http://localhost:5000`

### API Endpoints

#### 1. Execute a Flow

**POST** `/flow/execute`

Execute a flow from JSON definition.

**Request:**
```bash
curl -X POST http://localhost:5000/flow/execute \
  -H "Content-Type: application/json" \
  -d @sample_flow.json
```

**Response:**
```json
{
  "execution_id": "uuid-here",
  "flow_id": "flow123",
  "status": "completed",
  "execution_history": [
    {
      "task_name": "task1",
      "status": "success",
      "message": "Data fetched successfully",
      "data": {...}
    },
    ...
  ],
  "start_time": "2026-01-14T10:30:00",
  "end_time": "2026-01-14T10:30:02"
}
```

#### 2. Get Flow Status

**GET** `/flow/status/<execution_id>`

Get the status of a running or completed flow.

**Request:**
```bash
curl http://localhost:5000/flow/status/<execution_id>
```

#### 3. Validate Flow

**POST** `/flow/validate`

Validate a flow JSON without executing it.

**Request:**
```bash
curl -X POST http://localhost:5000/flow/validate \
  -H "Content-Type: application/json" \
  -d @sample_flow.json
```

#### 4. Health Check

**GET** `/health`

Check if the service is running.

**Request:**
```bash
curl http://localhost:5000/health
```

## Flow JSON Format

```json
{
  "flow": {
    "id": "unique-flow-id",
    "name": "Flow name",
    "start_task": "task1",
    "tasks": [
      {
        "name": "task1",
        "description": "Task description"
      }
    ],
    "conditions": [
      {
        "name": "condition_name",
        "description": "Condition description",
        "source_task": "task1",
        "outcome": "success",
        "target_task_success": "task2",
        "target_task_failure": "end"
      }
    ]
  }
}
```

### Key Fields

- **id**: Unique identifier for the flow
- **name**: Human-readable flow name
- **start_task**: Name of the first task to execute
- **tasks**: Array of task definitions
- **conditions**: Array of routing conditions

## Creating Custom Tasks

1. **Inherit from TaskExecutor:**

```python
from task_executor import TaskExecutor, register_task
from models import TaskExecutionResult, TaskStatus

@register_task("my_custom_task")
class MyCustomTask(TaskExecutor):
    def execute(self, context):
        # Your task logic here
        return TaskExecutionResult(
            task_name="my_custom_task",
            status=TaskStatus.SUCCESS,
            message="Task completed",
            data={"result": "data"}
        )
```

2. **Import in app.py:**

```python
import my_custom_task  # Registers the task
```

3. **Use in flow JSON:**

```json
{
  "name": "my_custom_task",
  "description": "My custom task"
}
```

## Example: Sample Flow

The included `sample_flow.json` demonstrates a data processing pipeline:

1. **task1**: Fetch data from a source
2. **task2**: Process the fetched data
3. **task3**: Store the processed data

Each task checks the previous task's success before proceeding. If any task fails, the flow ends.

## Testing

### Success Scenario

```bash
# Execute the sample flow
curl -X POST http://localhost:5000/flow/execute \
  -H "Content-Type: application/json" \
  -d @sample_flow.json
```

Expected: All tasks succeed, flow completes with status "completed"

### Failure Scenario

Task1 has a 10% random failure rate. If it fails:
- Flow ends after task1
- Status: "failed"
- Error message included in response

## Logging

The application logs all flow execution steps:
- Task execution start/end
- Condition evaluation
- Routing decisions
- Errors and warnings

Check console output for detailed execution logs.

## Design Decisions

### Why Sequential Execution?
Tasks often depend on previous task results. Sequential execution ensures data consistency and simplifies debugging.

### Why Condition-Based Routing?
Conditions provide flexibility to handle success/failure scenarios and create branching workflows without hardcoding logic.

### Why Task Registry?
The registry pattern allows adding new task types without modifying core engine code, making the system extensible.

### Why Store Execution State?
Storing state enables status checking, debugging, and audit trails for workflow executions.

## License

MIT License
