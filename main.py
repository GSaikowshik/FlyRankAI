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
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM tasks")
            return cursor.fetchall()

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    with get_db() as conn:
        with conn.cursor() as cursor:
            # psycopg uses %s for safe parameter injection
            cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
            task = cursor.fetchone()
            if not task:
                raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
            return task
@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate):
    if not task.title or not task.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING *", 
                (task.title, False)
            )
            new_task = cursor.fetchone()
        conn.commit()
        return new_task

@app.put("/tasks/{task_id}")
def update_task(task_id: int, task_update: TaskUpdate):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
            existing_task = cursor.fetchone()
            
            if not existing_task:
                raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
                
            new_title = task_update.title if task_update.title is not None else existing_task["title"]
            if task_update.title is not None and not task_update.title.strip():
                raise HTTPException(status_code=400, detail="Title cannot be empty")
                
            new_done = task_update.done if task_update.done is not None else existing_task["done"]
            
            cursor.execute(
                "UPDATE tasks SET title = %s, done = %s WHERE id = %s RETURNING *", 
                (new_title, new_done, task_id)
            )
            updated_task = cursor.fetchone()
        conn.commit()
        return updated_task

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
                
            cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
        conn.commit()
        return