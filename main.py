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
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks")
    tasks = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tasks

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    task = cursor.fetchone()
    conn.close()
    
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return dict(task)
@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate):
    if not task.title or not task.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", (task.title, 0))
    conn.commit()
    
    task_id = cursor.lastrowid
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    new_task = cursor.fetchone()
    conn.close()
    
    return dict(new_task)
@app.put("/tasks/{task_id}")
def update_task(task_id: int, task_update: TaskUpdate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    existing_task = cursor.fetchone()
    
    if not existing_task:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
    new_title = task_update.title if task_update.title is not None else existing_task["title"]
    if task_update.title is not None and not task_update.title.strip():
        conn.close()
        raise HTTPException(status_code=400, detail="Title cannot be empty")
        
    new_done = task_update.done if task_update.done is not None else existing_task["done"]
    
    cursor.execute("UPDATE tasks SET title = ?, done = ? WHERE id = ?", (new_title, new_done, task_id))
    conn.commit()
    
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    updated_task = cursor.fetchone()
    conn.close()
    return dict(updated_task)

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return