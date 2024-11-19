from fastapi import APIRouter, Response, status, Depends
from schemas import UserBase, UserDisplay, UserBase2
from fastapi import FastAPI, HTTPException, Depends
from typing import List
from db import db_user
from db.database import get_db

router = APIRouter(prefix="/user", tags=["user_router"])


# create
@router.post("/", response_model=UserDisplay)
def create_user(user: UserBase, db=Depends(get_db)):
    return db_user.create_user(db, user)


# get_all
@router.get("/", response_model=List[UserDisplay])
def get_all_users(db=Depends(get_db)):
    return db_user.get_all_users(db)


# get_one
@router.get("/{id}", response_model=UserDisplay)
def get_user(id: int, db=Depends(get_db)):
    return db_user.get_user(id, db)


# delete
@router.get("/delete/{id}")
def delete_user(id: int, db=Depends(get_db)):
    return db_user.delete_user(id, db)


# update
@router.post("/update/{id}", )
def update_user(id: int, user: UserBase2, db=Depends(get_db)):
    return db_user.update_user(id, db, user)

#
