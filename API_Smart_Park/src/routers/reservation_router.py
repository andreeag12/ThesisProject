from fastapi import APIRouter, HTTPException, Query
from pydantic import EmailStr
from typing import Optional
from datetime import date, time, datetime
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError
from src.imports.dynamodb_helper import get_table
from src.models.reservation import Reservation

reservation_router = APIRouter(prefix="/reservations", tags=["Reservations"])

def time_str_to_obj(t: str) -> time:
    return datetime.strptime(t, "%H:%M:%S").time()

def ranges_overlap(start1: time, end1: time, start2: time, end2: time) -> bool:
    return max(start1, start2) < min(end1, end2)

@reservation_router.post("/", status_code=201)
async def create_reservation(reservation: Reservation):
    table = get_table("Reservations")

    reservation_id = f"{reservation.email}#{reservation.date}#{reservation.parking_spot_id}#{reservation.hour_range[0].isoformat()}-{reservation.hour_range[1].isoformat()}"

    try:
        response = table.scan(
            FilterExpression=Attr("email").eq(reservation.email) & Attr("date").eq(reservation.date.isoformat())
        )
        existing_reservations = response.get("Items", [])

        new_start, new_end = reservation.hour_range

        for existing in existing_reservations:
            existing_start = time_str_to_obj(existing["hour_range"][0])
            existing_end = time_str_to_obj(existing["hour_range"][1])
            if ranges_overlap(new_start, new_end, existing_start, existing_end):
                raise HTTPException(
                    status_code=400,
                    detail=f"Time range overlaps with existing reservation from {existing_start} to {existing_end}"
                )

        item = {
            "reservation_id": reservation_id,
            "email": reservation.email,
            "car_plate": reservation.car_plate,
            "parking_spot_id": reservation.parking_spot_id,
            "date": reservation.date.isoformat(),
            "hour_range": [
                new_start.isoformat(),
                new_end.isoformat()
            ],
            "status": reservation.status or "pending"
        }

        table.put_item(
            Item=item,
            ConditionExpression="attribute_not_exists(reservation_id)"
        )
        return {"message": "Reservation created", "reservation": item}

    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise HTTPException(status_code=400, detail="Reservation already exists")
        raise HTTPException(status_code=500, detail=f"AWS error: {e.response['Error']['Message']}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@reservation_router.get("/{reservation_id}")
async def get_reservation(reservation_id: str):
    table = get_table("Reservations")
    try:
        response = table.get_item(Key={"reservation_id": reservation_id})
        item = response.get("Item")
        if not item:
            raise HTTPException(status_code=404, detail="Reservation not found")
        return item
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"AWS error: {e.response['Error']['Message']}")


@reservation_router.get("/")
async def get_reservations_by_email(email: EmailStr = Query(...)):
    table = get_table("Reservations")
    try:
        response = table.scan(FilterExpression=Attr("email").eq(email))
        items = response.get("Items", [])
        return items
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"AWS error: {e.response['Error']['Message']}")


@reservation_router.put("/{reservation_id}")
async def update_reservation_status(reservation_id: str, status: str):
    table = get_table("Reservations")
    try:
        response = table.update_item(
            Key={"reservation_id": reservation_id},
            UpdateExpression="SET #st = :s",
            ExpressionAttributeNames={"#st": "status"},
            ExpressionAttributeValues={":s": status},
            ConditionExpression="attribute_exists(reservation_id)",
            ReturnValues="ALL_NEW"
        )
        return {"message": "Reservation updated", "reservation": response["Attributes"]}
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise HTTPException(status_code=404, detail="Reservation not found")
        raise HTTPException(status_code=500, detail=f"AWS error: {e.response['Error']['Message']}")


@reservation_router.delete("/{reservation_id}", status_code=204)
async def delete_reservation(reservation_id: str):
    table = get_table("Reservations")
    try:
        table.delete_item(
            Key={"reservation_id": reservation_id},
            ConditionExpression="attribute_exists(reservation_id)"
        )
        return {"message": "Reservation deleted"}
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise HTTPException(status_code=404, detail="Reservation not found")
        raise HTTPException(status_code=500, detail=f"AWS error: {e.response['Error']['Message']}")
