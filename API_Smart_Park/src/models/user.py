from typing import List, Optional
from src.models.car import CarPlate
from pydantic import BaseModel, Field, EmailStr


class UserRegistration(BaseModel):
    name: str
    email: str
    phone: str
    password: str
    car_plate_ids: List[str] = Field(..., example=["ABC123", "XYZ789"])
    role: str = "regular"


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    role: Optional[str] = None


class UserUpdateProfile(BaseModel):
    name: Optional[str]
    email: Optional[EmailStr]
    phone: Optional[str]
    car_plate_ids: Optional[List[str]]