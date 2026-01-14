# Flow Manager - Expected Deliverables Documentation

This document addresses the expected deliverables

---

## 1. Explanation of the Flow Design

### How do the tasks depend on one another?

Tasks are **chained through conditions** defined in the flow JSON. Dependencies are established using a condition-based routing system:

**Dependency Mechanism:**
- Each **Condition** specifies a `source_task` (the task whose result triggers the routing decision)
- Each Condition defines `target_task_success` (next task if source succeeds) and `target_task_failure` (where to go if source fails)
- Tasks execute **sequentially**, not in parallel
- A task can only execute if the previous task in the chain completed

**Example from sample_flow.json:**
```
task1 (Fetch Data)
  └─ Condition: If task1 succeeds → task2, else → end
       └─ task2 (Process Data)
            └─ Condition: If task2 succeeds → task3, else → end
                 └─ task3 (Store Data)
                      └─ end
```

**Data Dependencies:**
- Tasks receive execution context containing results from all previous tasks
- Tasks can access previous task results via `context["execution_history"]`
- Example: task2 retrieves task1's fetched data to process it
- Example: task3 retrieves task2's processed data to store it

---

### How is the success or failure of a task evaluated?

Task success/failure is evaluated through a **two-level system**:

**Level 1: Task Execution (Runtime Evaluation)**

Each task returns a `TaskExecutionResult` object with:
```python
{
    "task_name": "task1",
    "status": TaskStatus.SUCCESS | TaskStatus.FAILURE,  # Enum value
    "data": <task output>,
    "message": <description>,
    "timestamp": <execution time>
}
```

**How tasks determine their own status:**
- Tasks execute their logic within a `try-except` block
- **Success criteria**: Task logic completes without exceptions AND business logic succeeds
- **Failure criteria**: Exception thrown OR business validation fails
- Example in task1: Returns `SUCCESS` if data fetched, `FAILURE` if connection timeout

**Level 2: Condition Evaluation (Routing Decision)**

The `ConditionEvaluator` compares task results against condition definitions:

```python
# Condition definition from JSON
{
    "source_task": "task1",           # Which task to evaluate
    "outcome": "success",              # Expected outcome
    "target_task_success": "task2",   # Route if matched
    "target_task_failure": "end"      # Route if not matched
}
```

**Evaluation logic:**
1. Get the `TaskExecutionResult` for the `source_task`
2. Compare `result.status` with condition's `outcome` expectation
3. If match → route to `target_task_success`
4. If no match → route to `target_task_failure`

---

### What happens if a task fails or succeeds?

**When a Task SUCCEEDS:**

1. **Result Recorded**: Task result added to `FlowExecutionState.execution_history`
2. **Condition Evaluated**: System finds conditions where `source_task` matches the succeeded task
3. **Routing Decision**: 
   - If condition expects "success" → route to `target_task_success`
   - Next task name determined
4. **Context Prepared**: Execution context updated with latest results
5. **Next Task Executed**: Orchestrator executes the next task with full context
6. **Flow Continues**: Process repeats until task routes to "end"

**Flow State on Success:**
```python
{
    "status": FlowStatus.RUNNING,    # While executing
    "current_task": "task2",         # Currently executing task
    "execution_history": [           # All completed tasks
        {...task1_result...}
    ]
}
```

**When a Task FAILS:**

1. **Failure Recorded**: Task failure result added to execution history
2. **Condition Evaluated**: System finds conditions for the failed task
3. **Routing Decision**:
   - Routes to `target_task_failure` (typically "end")
   - Flow terminates
4. **Flow Status Updated**:
   ```python
   {
       "status": FlowStatus.FAILED,
       "error_message": <task failure message>,
       "end_time": <timestamp>
   }
   ```
5. **No Further Execution**: Remaining tasks are NOT executed
6. **Response Returned**: API returns HTTP 500 with failure details

**Example Scenarios:**

**Scenario 1: All tasks succeed**
```
task1 SUCCESS → Condition evaluates → task2 SUCCESS → Condition evaluates → task3 SUCCESS → end
Final status: "completed"
```

**Scenario 2: task2 fails**
```
task1 SUCCESS → Condition evaluates → task2 FAILURE → Condition evaluates → "end"
Final status: "failed", error: "task2 failure message"
Task3 is NOT executed
```
