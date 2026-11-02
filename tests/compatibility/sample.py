"""Small generated-style projects for the Integration & Compatibility Engine tests: a task API contract, a backend that
implements it, a frontend that uses it, a SQL schema - and the usual ways independently generated components disagree."""

from pathlib import Path
from typing import Dict

TASK = {"type": "object", "properties": {"id": {"type": "integer"}, "title": {"type": "string"}, "done": {"type": "boolean"}},
        "required": ["id", "title", "done"]}

CONTRACT = {
    "api": {"name": "tasks", "endpoints": [
        {"method": "GET", "path": "/api/tasks", "auth": "none",
         "responses": {"200": {"content_type": "application/json", "schema": {"type": "array", "items": TASK}}}},
        {"method": "POST", "path": "/api/tasks", "auth": "bearer",
         "request_schema": {"type": "object", "properties": {"title": {"type": "string"}, "done": {"type": "boolean"}},
                            "required": ["title"]},
         "responses": {"201": {"content_type": "application/json", "schema": TASK}},
         "errors": {"401": {"description": "no token"}, "422": {"description": "invalid body"}}},
        {"method": "GET", "path": "/api/tasks/{task_id}", "auth": "none", "path_params": {"task_id": {"type": "integer"}},
         "responses": {"200": {"content_type": "application/json", "schema": TASK}},
         "errors": {"404": {"description": "no such task"}}},
    ]},
    "entities": [{"name": "Task", "table": "tasks", "fields": [
        {"name": "id", "type": "integer", "primary_key": True},
        {"name": "title", "type": "string"},
        {"name": "done", "type": "boolean"},
        {"name": "owner_id", "type": "integer", "references": "User.id"}]},
        {"name": "User", "table": "users", "fields": [{"name": "id", "type": "integer", "primary_key": True},
                                                      {"name": "email", "type": "string", "format": "email"}]}],
    "auth": {"scheme": "bearer"},
    "error_format": {"type": "object", "properties": {"detail": {}}, "required": ["detail"]},
    "datetime_format": "iso8601",
    "requirements": ["Users create tasks with a title", "Anyone can list tasks and read one task"],
}

BACKEND = '''from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPBearer
from pydantic import BaseModel

app = FastAPI(title="Tasks")
bearer = HTTPBearer()
_tasks: dict = {}


def get_current_user(token=Depends(bearer)):
    return {"id": 1}


class TaskIn(BaseModel):
    title: str
    done: bool = False


class Task(BaseModel):
    id: int
    title: str
    done: bool


@app.get("/api/tasks", response_model=List[Task])
def list_tasks():
    return list(_tasks.values())


@app.post("/api/tasks", response_model=Task, status_code=201)
def create_task(body: TaskIn, user=Depends(get_current_user)):
    task_id = len(_tasks) + 1
    _tasks[task_id] = {"id": task_id, "title": body.title, "done": body.done}
    return _tasks[task_id]


@app.get("/api/tasks/{task_id}", response_model=Task)
def get_task(task_id: int):
    if task_id not in _tasks:
        raise HTTPException(status_code=404, detail="no such task")
    return _tasks[task_id]
'''

API_JS = '''import axios from 'axios';

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api' });
api.interceptors.request.use((config) => {
  config.headers.Authorization = `Bearer ${localStorage.getItem('token')}`;
  return config;
});

export const listTasks = async () => {
  const { data } = await api.get('/tasks');
  return data;
};
export const createTask = (title) => api.post('/tasks', { title, done: false });
export const getTask = (id) => api.get(`/tasks/${id}`);
'''

APP_JSX = '''import { useEffect, useState } from 'react';
import { createTask, listTasks } from './api';

export default function App() {
  const [tasks, setTasks] = useState([]);
  useEffect(() => { listTasks().then(setTasks); }, []);
  return <ul>{tasks.map((t) => <li key={t.id}>{t.title}</li>)}<button onClick={() => createTask('x')}>add</button></ul>;
}
'''

# The frontend agent's version that disagrees with the contract: wrong path (no /api), wrong method, a field named
# taskName where the contract says title, no Authorization header on the protected call.
APP_JSX_BROKEN = '''import { useEffect, useState } from 'react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function App() {
  const [tasks, setTasks] = useState([]);
  useEffect(() => {
    fetch(`${API}/tasks`).then((r) => r.json()).then((data) => setTasks(data));
  }, []);
  const add = async (name) => {
    await fetch(`${API}/api/tasks`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ taskName: name }) });
  };
  return <ul>{tasks.map((t) => <li key={t.id}>{t.taskName}</li>)}<button onClick={() => add('x')}>add</button></ul>;
}
'''

PACKAGE_JSON = '{"name": "tasks-ui", "private": true, "scripts": {"build": "vite build"}, "dependencies": {"axios": "^1.6.0", "react": "^18.2.0"}}\n'

SCHEMA_SQL = '''CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  email TEXT NOT NULL
);

CREATE TABLE tasks (
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  done BOOLEAN NOT NULL DEFAULT 0,
  owner_id INTEGER NOT NULL REFERENCES users(id)
);
'''

# The database agent's version: no owner relationship, done stored as text, title nullable.
SCHEMA_SQL_BROKEN = '''CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  email TEXT NOT NULL
);

CREATE TABLE tasks (
  id INTEGER PRIMARY KEY,
  title TEXT,
  done TEXT NOT NULL,
  owner_id INTEGER NOT NULL
);
'''

MODELS_PY = '''from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False)


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    done = Column(Boolean, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    priority = Column(Integer, nullable=False)
'''


def write(root: Path, files: Dict[str, str]) -> Path:
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return root


def project(root: Path, backend: str = BACKEND, app: str = APP_JSX, schema: str = SCHEMA_SQL, extra=None) -> Path:
    files = {"backend/main.py": backend, "frontend/package.json": PACKAGE_JSON, "frontend/src/api.js": API_JS,
             "frontend/src/App.jsx": app, "database/schema.sql": schema}
    files.update(extra or {})
    return write(root, {k: v for k, v in files.items() if v is not None})
