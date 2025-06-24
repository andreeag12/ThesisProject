from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from boto3.dynamodb.conditions import Key
from src.imports.dynamodb_helper import get_table, hash_password
from src.models.user import UserRegistration, UserLogin
import jwt

register_router = APIRouter(prefix="/register", tags=["Register"])
login_router = APIRouter(prefix="/login", tags=["Login"])

# Secret key & algorithm
SECRET_KEY = 'td_WKP0BViNq3n4t-z9kmEcOexJOhGZfDWseUnO0rPY'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30


@register_router.post("/")
async def register_user(user_data: UserRegistration):
    table = get_table("Users")
    encrypted_password = hash_password(user_data.password)

    try:
        table.put_item(
            Item={
                "email": user_data.email,    # email as primary key here
                "name": user_data.name,
                "phone": user_data.phone,
                "car_plate_ids": user_data.car_plate_ids,
                "role": user_data.role,
                "password_hash": encrypted_password
            },
            ConditionExpression="attribute_not_exists(email)"  # ensure email is unique
        )
        return {"email": user_data.email, "message": "User registered successfully"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"User already exists or invalid input: {str(e)}")


@login_router.post("/")
async def login_user(user_data: UserLogin):
    table = get_table("Users")

    encrypted_password = hash_password(user_data.password)

    try:
        response = table.get_item(Key={"email": user_data.email})  # get by email
        user = response.get("Item")

        if not user or user.get('password_hash') != encrypted_password:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        expiration = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": user["email"],
            "exp": expiration,
            "role": user.get("role")
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "email": user.get("email"),
                "name": user.get("name"),
                "phone": user.get("phone"),
                "car_plate_ids": user.get("car_plate_ids", []),
                "role": user.get("role"),
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")
