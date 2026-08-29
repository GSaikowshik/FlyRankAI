from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import status
from pydantic import BaseModel
from typing import Optional
import sqlite3

class TaskCreate(BaseModel):
    title: str
class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None

app = FastAPI(title="Task API", version="1.0")



def get_db():
    conn = sqlite3.connect("tasks.db")
    conn.row_factory = sqlite3.Row 
    return conn
def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT 0
        )
    ''')
    cursor.execute("SELECT COUNT(*) FROM tasks")
    if cursor.fetchone()[0] == 0:
        examples = [
            ("Set up FastAPI", 1),
            ("Build CRUD endpoints", 0),
            ("Connect to SQLite", 0)
        ]
        cursor.executemany("INSERT INTO tasks (title, done) VALUES (?, ?)", examples)
    conn.commit()
    conn.close()

init_db()


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
@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate):
    global next_id
    if not task.title or not task.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    
    new_task = {"id": next_id, "title": task.title, "done": False}
    tasks.append(new_task)
    next_id += 1
    return new_task
@app.put("/tasks/{task_id}")
def update_task(task_id: int, task_update: TaskUpdate):
    for task in tasks:
        if task["id"] == task_id:
            if task_update.title is not None:
                if not task_update.title.strip():
                    raise HTTPException(status_code=400, detail="Title cannot be empty")
                task["title"] = task_update.title
            if task_update.done is not None:
                task["done"] = task_update.done
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    for i, task in enumerate(tasks):
        if task["id"] == task_id:
            del tasks[i]
            return
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")