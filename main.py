import os
import psycopg
from psycopg.rows import dict_row
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if not url or not key:
    raise ValueError("SUPABASE_URL or SUPABASE_KEY is missing from environment variables.")

supabase: Client = create_client(url, key)

DATABASE_URL = os.environ.get("DATABASE_URL")

app = FastAPI(title="Auth API")

class TaskCreate(BaseModel):
    title: str

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None

class AuthCredentials(BaseModel):
    email: str
    password: str

def get_db():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

def init_db():
    try:
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
        print("✅ Database connected and initialized.")
    except Exception as e:
        print(f"⚠️ Warning: Could not connect to Postgres database. Error: {e}")

#init_db()
@app.get("/")
def read_root():
    return {"message": "Server running and connected to Supabase"}

@app.get("/health")
def get_health():
    return {"status": "ok"}
@app.post("/auth/signup", status_code=status.HTTP_201_CREATED)
def signup(credentials: AuthCredentials):
    # Validate missing or empty fields
    if not credentials.email or not credentials.email.strip() or not credentials.password or not credentials.password.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Email and password are required"}
        )

    try:
        response = supabase.auth.sign_up({
            "email": credentials.email.strip(),
            "password": credentials.password
        })
        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Failed to create user"}
            )
        return {
            "message": "User created successfully",
            "user": {
                "id": response.user.id,
                "email": response.user.email
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": str(e)}
        )

@app.post("/auth/login", status_code=status.HTTP_200_OK)
def login(credentials: AuthCredentials):
    # Validate missing or empty fields
    if not credentials.email or not credentials.email.strip() or not credentials.password or not credentials.password.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Email and password are required"}
        )

    try:
        response = supabase.auth.sign_in_with_password({
            "email": credentials.email.strip(),
            "password": credentials.password
        })
        if not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Invalid login credentials"}
            )
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "token_type": "bearer"
        }
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid login credentials"}
        )

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