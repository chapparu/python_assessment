from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from typing import List

DATABASE_URL = "postgresql://postgres:ROOT#123@localhost/new_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    profile = relationship("Profile", back_populates="user")


class Profile(Base):
    __tablename__ = "profile"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    profile_picture = Column(String)
    user = relationship("User", back_populates="profile")


Base.metadata.create_all(bind=engine)


class UserCreate(BaseModel):
    first_name: str
    email: str
    phone: str
    password: str
    profile_picture: str


class UserResponse(BaseModel):
    id: int
    first_name: str
    email: str
    phone: str
    profile_picture: str


app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/register/", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_email = db.query(User).filter(User.email == user.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    existing_phone = db.query(User).filter(User.phone == user.phone).first()
    if existing_phone:
        raise HTTPException(status_code=400, detail="Phone number already registered")

    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    db_profile = Profile(user_id=db_user.id, profile_picture=user.profile_picture)
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)

    return db_user


@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    user_details = UserResponse(
        id=db_user.id,
        first_name=db_user.first_name,
        email=db_user.email,
        phone=db_user.phone,
        profile_picture=db_user.profile.profile_picture
    )
    return user_details
