from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, engine, get_db
from .security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

Base.metadata.create_all(bind=engine)  # tables bana do agar nahi hain

app = FastAPI(title="TaskFlow API")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> models.User:
    user_id = decode_access_token(token)
    user = db.get(models.User, user_id) if user_id else None
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    return user


@app.post("/auth/register", response_model=schemas.UserOut, status_code=201)
def register(data: schemas.UserCreate, db: Session = Depends(get_db)):
    exists = db.scalar(select(models.User).where(models.User.email == data.email))
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    user = models.User(email=data.email, hashed_password=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/auth/login", response_model=schemas.Token)
def login(
    form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = db.scalar(select(models.User).where(models.User.email == form.username))
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong email or password")
    return schemas.Token(access_token=create_access_token(user.id))


def get_own_task(task_id: int, db: Session, user: models.User) -> models.Task:
    task = db.get(models.Task, task_id)
    # 404 dete hain (403 nahi) taaki dusre ke task ka existence leak na ho
    if task is None or task.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    return task


@app.get("/tasks", response_model=list[schemas.TaskOut])
def list_tasks(
    done: bool | None = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    query = select(models.Task).where(models.Task.owner_id == user.id)
    if done is not None:
        query = query.where(models.Task.done == done)
    return db.scalars(query.order_by(models.Task.created_at.desc())).all()


@app.post("/tasks", response_model=schemas.TaskOut, status_code=201)
def create_task(
    data: schemas.TaskCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    task = models.Task(**data.model_dump(), owner_id=user.id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@app.patch("/tasks/{task_id}", response_model=schemas.TaskOut)
def update_task(
    task_id: int,
    data: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    task = get_own_task(task_id, db, user)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    task = get_own_task(task_id, db, user)
    db.delete(task)
    db.commit()


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}


# Frontend sabse last me mount hota hai, warna API routes dhak jayenge
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
