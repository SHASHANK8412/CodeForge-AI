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

# Folder Structure

```
todo-app/
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── App.js
│   │   ├── index.js
│   └── package.json
├── backend/
│   ├── app.py
│   ├── models/
│   │   ├── user.py
│   │   ├── task.py
│   ├── schemas/
│   │   ├── user.py
│   │   ├── task.py
│   ├── routes/
│   │   ├── auth_routes.py
│   │   ├── task_routes.py
│   └── requirements.txt
├── database/
│   ├── config.py
│   └── db.py
└── .env
```

# Database Choice

- **MongoDB**
  - Document model for flexible schema
  - High performance and scalability
  - Integrated with FastAPI via PyMongo or MongooDB Python Driver
  
# API Design

- **User Authentication APIs**
  - POST /auth/signup: Register new user
  - POST /auth/login: Authenticate user, generate JWT token
  
- **Task Management APIs**
  - GET /tasks: Retrieve all tasks for a user
  - POST /tasks: Create a new task
  - PUT /tasks/{task_id}: Update an existing task
  - DELETE /tasks/{task_id}: Delete a task
  - PATCH /tasks/{task_id}/category: Change task category
  - PATCH /tasks/{task_id}/due_date: Set or update due date
  
- **Notifications API**
  - POST /notifications/send: Send notification for a specific task deadline