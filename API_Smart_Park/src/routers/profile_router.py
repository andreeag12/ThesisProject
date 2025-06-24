from fastapi import APIRouter, HTTPException, Body
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from src.imports.dynamodb_helper import get_table

profile_router = APIRouter(prefix="/profile", tags=["Profile"])

class UserUpdateProfile(BaseModel):
    email: EmailStr
    name: Optional[str]
    phone: Optional[str]
    car_plate_ids: Optional[List[str]]

@profile_router.put("/update/")
async def update_profile(profile: UserUpdateProfile):
    table = get_table("Users")

    try:
        result = table.get_item(Key={"email": profile.email})
        user = result.get("Item")

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        data = profile.dict(exclude={"email"}, exclude_none=True)
        if not data:
            return {"message": "Nothing to update"}

        update_expr_parts = []
        expr_attr_vals = {}
        expr_attr_names = {}

        for i, (key, value) in enumerate(data.items()):
            attr_name_placeholder = f"#attr{i}"
            attr_value_placeholder = f":val{i}"
            update_expr_parts.append(f"{attr_name_placeholder} = {attr_value_placeholder}")
            expr_attr_names[attr_name_placeholder] = key
            expr_attr_vals[attr_value_placeholder] = value

        update_expr = "SET " + ", ".join(update_expr_parts)

        table.update_item(
            Key={"email": profile.email},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_vals
        )

        return {"message": "Profile updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")
