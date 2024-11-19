from sqlalchemy.orm.session import Session
from schemas import UserBase, UserBase2
from db.models import DbUser
from db.hash import Hash
from fastapi.exceptions import HTTPException
from fastapi import status
from db import models


# create user
def create_user(db: Session, request: UserBase):
    user = DbUser(username=request.username,
                  email=request.email,
                  password=Hash.bcrypt(request.password)
                  )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# read_all

def get_all_users(db: Session):
    return db.query(DbUser).all()


# read_one

def get_user(user_id: int, db: Session):
    return db.query(DbUser).filter(DbUser.id == user_id).first()


# read_one(username)

def get_user_by_username(username: str, db: Session):
    user = db.query(DbUser).filter(DbUser.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="user not found")
    return user


# delete_user

def delete_user(user_id: int, db: Session):
    user = get_user(user_id, db)
    db.delete(user)
    db.commit()
    return "ok"


# update_user
def update_user(user_id: int, db: Session, request: UserBase2):
    user = db.query(DbUser).filter(DbUser.id == user_id)
    user.update({
        DbUser.username: request.username,
        DbUser.email: request.email,
        DbUser.password: Hash.bcrypt(request.password)

    })
    db.commit()
    return "ok"


def get_device_inspections_by_user(db: Session, user_id: int):
    return db.query(models.DeviceInspection).filter(models.DeviceInspection.user_id == user_id).all()


def get_user_by_username_password(db: Session, username: str, password: str):
    return db.query(models.DbUser).filter(models.DbUser.username == username,
                                          models.DbUser.password == password).first()
