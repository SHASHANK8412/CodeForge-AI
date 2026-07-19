from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Optional

# Initialize FastAPI app
app = FastAPI()

# Dummy database for demonstration purposes
fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
    }
}

# Security settings
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2 password bearer scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token data model
class Token(BaseModel):
    access_token: str
    token_type: str

# Token data with username
class TokenData(BaseModel):
    username: Optional[str] = None

# User model
class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

# User schema for database
class UserInDB(User):
    hashed_password: str

# Function to verify password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Function to get user by username
def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

# Function to authenticate user
def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

# Function to create access token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Function to get current user from token
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

# Function to get current active user
async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Authentication routes
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Task routes (placeholder for actual implementation)
@app.get("/tasks")
async def read_tasks(current_user: User = Depends(get_current_active_user)):
    # Placeholder logic to retrieve tasks for the user
    return [{"task_id": 1, "title": "Task 1", "category": "personal"}]

@app.post("/tasks")
async def create_task(task_data: dict, current_user: User = Depends(get_current_active_user)):
    # Placeholder logic to create a new task
    return {"task_id": 2, "title": task_data["title"], "category": task_data.get("category", "personal")}

@app.put("/tasks/{task_id}")
async def update_task(task_id: int, task_data: dict, current_user: User = Depends(get_current_active_user)):
    # Placeholder logic to update an existing task
    return {"task_id": task_id, "title": task_data["title"], "category": task_data.get("category", "personal")}

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int, current_user: User = Depends(get_current_active_user)):
    # Placeholder logic to delete a task
    return {"task_id": task_id, "message": "Task deleted"}