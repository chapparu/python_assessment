from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from pymongo import MongoClient
from pydantic import BaseModel
from typing import List


# PostgreSQL connection setup
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String
from sqlalchemy.testing import db

DATABASE_URL = "postgresql://postgres:ROOT#123@localhost/new_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class UserPostgreSQL(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String)
    hashed_password = Column(String)


# MongoDB connection setup
mongo_client = MongoClient("mongodb://localhost:27017/")
mongo_db = mongo_client["fastapi_db"]
mongo_collection = mongo_db["users"]


class UserMongoDB(BaseModel):
    user_id: int
    profile_picture: str


app = FastAPI()


# Dependency to get PostgreSQL database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/register/")
def register_user(user: UserPostgreSQL, db: Session = Depends(get_db)):
    db_user = db.query(UserPostgreSQL).filter(UserPostgreSQL.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    db.add(user)
    db.commit()
    db.refresh(user)

    user_id = user.id

    # Store profile picture in MongoDB
    profile_picture = UserMongoDB(user_id=user_id, profile_picture=user.profile_picture)
    mongo_collection.insert_one(profile_picture.dict())

    return {"message": "User registered successfully"}


@app.get("/users/{user_id}")
def get_user(user_id: int):
    # Retrieve user details from PostgreSQL
    db_user = db.query(UserPostgreSQL).filter(UserPostgreSQL.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Retrieve profile picture from MongoDB
    mongo_user = mongo_collection.find_one({"user_id": user_id})
    if not mongo_user:
        raise HTTPException(status_code=404, detail="Profile picture not found")

    user_details = {
        "id": db_user.id,
        "first_name": db_user.first_name,
        "email": db_user.email,
        "phone": db_user.phone,
        "profile_picture": mongo_user["profile_picture"]
    }
    return user_details
