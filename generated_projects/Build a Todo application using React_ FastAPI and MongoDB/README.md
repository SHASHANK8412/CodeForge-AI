# Build a Todo application using React, FastAPI and MongoDB

Generated autonomously with 🚀 **AIForge** - Multi-Agent AI Software Engineering Platform.

---

## 📋 Project Overview
This is a production-ready, containerized full-stack application built using **React** for the frontend interface and **FastAPI** for the backend logic and services.

### Core Features
- Complete user layout interface using React and modern CSS styling.
- RESTful API controllers with automatic document models using FastAPI.
- Robust database persistence mapping.
- Pytest testing suite coverage checking.

---

## 🏗️ System Architecture
The application runs on a decoupled, parallel layout structured as follows:
- **Frontend App**: SPA built with React and bundled via Vite.
- **Backend App**: REST API service built with FastAPI.
- **Database Layer**: Structured schema matching model requirements.

```
                  ┌─────────────────┐
                  │   Web Browser   │
                  └────────┬────────┘
                           │ HTTP Request
                           ▼
                  ┌─────────────────┐
                  │ React SPA (80)  │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ FastAPI (8000)  │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  Database Layer │
                  └─────────────────┘
```

### Plan Snippet
```markdown
# Features
- User authentication (login/signup)
- Task creation, editing, deletion
- Task categorization (personal/work)
- Due date and time setting
- Notification system for task deadlines

# Modules
- Frontend: React
  - Login/Signup form
  - Todo list interface
  - CRUD operations for tasks
- Backend: FastAPI
  - User management API
  - Task management API
...
```

### Architecture Snippet
```markdown
# Architecture

- **Frontend**: React.js
  - Single Page Application (SPA)
  - User Interface components: Login/Signup form, Todo list interface, CRUD operations for tasks
  
- **Backend**: FastAPI
  - RESTful API framework
  - User management APIs: Create, Read, Update, Delete (CRUD) users
  - Task management APIs: CRUD tasks, categorization, due date setting

- **Database**: MongoDB
  - Document-oriented NoSQL database
  - Users collection: Store user data with authentication details
  - Tasks collection: Store task data including categories and due dates
...
```

---

## 📁 Folder Structure
```text
Build a Todo application using React, FastAPI and MongoDB/
├── frontend/             # React Vite SPA Source
│   ├── src/
│   │   ├── components/   # Shared layout elements
│   │   └── App.jsx       # Main App view routing
│   ├── package.json      # NPM dependencies configuration
│   └── Dockerfile        # Production nginx configuration
│
├── backend/              # FastAPI Application Source
│   ├── main.py           # App routing entry point
│   ├── requirements.txt  # Python pip dependencies
│   └── Dockerfile        # Backend service deployment
│
├── database/             # Relational Database persistence
│   └── schema.sql        # Table structures initialization script
│
├── tests/                # Testing suite folder
│   └── test_app.py       # Automated testing scripts
│
├── docker-compose.yml    # Main stack container setup orchestration
├── .env.example          # Environment variables template
└── README.md             # This instruction documentation
```

---

## ⚙️ Installation & Running

### Option 1: Running with Docker Compose (Recommended)
Make sure you have Docker installed on your host machine, then run:

```bash
# 1. Build and run all services in the background
docker compose up --build -d

# 2. View streaming logs
docker compose logs -f
```
The Frontend will be accessible at: `http://localhost:80`
The Backend API documentation will be accessible at: `http://localhost:8000/docs`

---

### Option 2: Running Locally

#### 1. Setup Backend
Ensure python 3.10+ is installed on your host:

```bash
cd backend
python -m venv .venv
# On Windows
.venv\Scripts\activate
# On macOS/Linux
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Run server
uvicorn backend.main:app --reload --port 8000
```

#### 2. Setup Frontend
Ensure Node.js 18+ is installed on your host:

```bash
cd frontend
npm install
npm run dev
```
The local Vite server will boot at: `http://localhost:5173`

---

## 🔒 Environment Variables
Copy `.env.example` to `.env` in the root folder and configure:
- `PORT`: Port server key
- `DATABASE_URL`: Connection string URL
- `JWT_SECRET`: Authorization encryption key
- `OLLAMA_MODEL`: Target LLM model name

---

## 🧪 Testing
To execute backend testing suites locally:

```bash
cd backend
pytest tests/
```

---

## 📜 License
This project is licensed under the MIT License. See the LICENSE file for details.
