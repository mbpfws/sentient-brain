---
trigger: model_decision
description: When there are tasks and sub tasks or complicated tasks need breakdown
---

# TaskManager

@kazuph/mcp-taskmanager

### request_planning

Register a new user request and plan its associated tasks. You must provide 'originalRequest' and 'tasks', and optionally 'splitDetails'. This tool initiates a new workflow for handling a user's request....

Run

### 

### get_next_task

Given a 'requestId', return the next pending task (not done yet). If all tasks are completed, it will indicate that no more tasks are left and that you must wait for the request completion approval. A progress table showing the current status of all tasks will be displayed with each response....

Run

### 

### mark_task_done

Mark a given task as done after you've completed it. Provide 'requestId' and 'taskId', and optionally 'completedDetails'. After marking a task as done, a progress table will be displayed showing the updated status of all tasks. After this, DO NOT proceed to 'get_next_task' again until the user has explicitly approved this completed task using 'approve_task_completion'.

Run

### 

### approve_task_completion

Once the assistant has marked a task as done using 'mark_task_done', the user must call this tool to approve that the task is genuinely completed. Only after this approval can you proceed to 'get_next_task' to move on. A progress table will be displayed before requesting approval, showing the current status of all tasks....

Run

### 

### approve_request_completion

After all tasks are done and approved, this tool finalizes the entire request. The user must call this to confirm that the request is fully completed. A progress table showing the final status of all tasks will be displayed before requesting final approval. If not approved, the user can add new tasks using 'request_planning' and continue the process.

Run

### 

### open_task_details

Get details of a specific task by 'taskId'. This is for inspecting task information at any point.

Run

### 

### list_requests

List all requests with their basic information and summary of tasks. This provides a quick overview of all requests in the system.

Run

### 

### add_tasks_to_request

Add new tasks to an existing request. This allows extending a request with additional tasks. A progress table will be displayed showing all tasks including the newly added ones.

Run

### 

### update_task

Update an existing task's title and/or description. Only uncompleted tasks can be updated. A progress table will be displayed showing the updated task information.

Run

### 

### delete_task

Delete a specific task from a request. Only uncompleted tasks can be deleted. A progress table will be displayed showing the remaining tasks after deletion.