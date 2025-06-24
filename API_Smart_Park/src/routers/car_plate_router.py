from fastapi import FastAPI, APIRouter, HTTPException, Body
from src.imports.dynamodb_helper import get_table

app = FastAPI()

car_plate_router = APIRouter(prefix="/car-plates", tags=["Car Plates"])


@car_plate_router.post("/{email}")
async def add_car_plate(email: str, new_plate: str = Body(..., embed=True)):
    """
    Add a new car plate to the user's car_plate_ids list.
    """
    table = get_table("Users")

    try:
        result = table.get_item(Key={"email": email})
        user = result.get("Item")

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        current_plates = user.get("car_plate_ids", [])

        if new_plate in current_plates:
            raise HTTPException(status_code=400, detail="Car plate already exists")

        current_plates.append(new_plate)

        table.update_item(
            Key={"email": email},
            UpdateExpression="SET car_plate_ids = :plates",
            ExpressionAttributeValues={":plates": current_plates}
        )

        return {"message": "Car plate added successfully", "car_plate_ids": current_plates}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add car plate: {str(e)}")


@car_plate_router.delete("/{email}/{plate_id}")
async def delete_car_plate(email: str, plate_id: str):
    """
    Delete a car plate from the user's car_plate_ids list.
    """
    table = get_table("Users")

    try:
        result = table.get_item(Key={"email": email})
        user = result.get("Item")

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        plates = user.get("car_plate_ids", [])

        if plate_id not in plates:
            raise HTTPException(status_code=404, detail="Car plate not found")

        plates.remove(plate_id)

        table.update_item(
            Key={"email": email},
            UpdateExpression="SET car_plate_ids = :plates",
            ExpressionAttributeValues={":plates": plates}
        )

        return {"message": "Car plate removed successfully", "car_plate_ids": plates}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove car plate: {str(e)}")


@car_plate_router.get("/{email}")
async def get_car_plates(email: str):
    """
    Get all car plates associated with the user.
    """
    table = get_table("Users")

    try:
        result = table.get_item(Key={"email": email})
        user = result.get("Item")

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {"car_plate_ids": user.get("car_plate_ids", [])}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch car plates: {str(e)}")


