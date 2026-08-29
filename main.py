import os
import psycopg
from psycopg.rows import dict_row
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL")

app = FastAPI(title="Task API", version="1.0")

class TaskCreate(BaseModel):
    title: str

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None

def get_db():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

def init_db():
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    done BOOLEAN NOT NULL DEFAULT FALSE
                )
            ''')
            cursor.execute("SELECT COUNT(*) FROM tasks")
            if cursor.fetchone()['count'] == 0:
                cursor.execute("INSERT INTO tasks (title, done) VALUES (%s, %s), (%s, %s), (%s, %s)", 
                               ("Set up Docker", True, "Connect Postgres", False, "Write Compose file", False))
        conn.commit()

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