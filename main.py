from fastapi import FastAPI
app = FastAPI(title="Task API", version="1.0")
from fastapi import HTTPException

tasks = [
    {"id": 1, "title": "Set up FastAPI", "done": True},
    {"id": 2, "title": "Build CRUD endpoints", "done": False},
    {"id": 3, "title": "Test in Swagger UI", "done": False},
]
next_id = 4


@app.get("/")
def get_root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health")
def get_health():
    return {"status": "ok"}
@app.get("/tasks")
def get_tasks():
    return tasks

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")