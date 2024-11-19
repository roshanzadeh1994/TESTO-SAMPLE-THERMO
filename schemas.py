from pydantic import BaseModel
from datetime import datetime, date
from typing import List, Optional


class DeviceInspectionInput(BaseModel):
    inspection_location: str    
    device_name: str
    inspection_date: date
    inspection_details: str
    kältepump: int
    user_id: int


class DeviceInspectionCreate(DeviceInspectionInput):
    pass


class DeviceInspection(DeviceInspectionInput):
    id: int
    user_id: int

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    username: str
    email: str
    password: str


class UserBase2(BaseModel):
    id: int
    username: str
    email: str
    password: str


class UserDisplay(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True


class User(BaseModel):
    username: str

    class Config:
        from_attributes = True


class UserId(BaseModel):
    id: int

    class Config:
        from_attributes = True


class UserAuth(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True


#

class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
