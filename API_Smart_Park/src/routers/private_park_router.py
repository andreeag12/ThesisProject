from fastapi import APIRouter, UploadFile, HTTPException, Form
from pathlib import Path
import shutil
from datetime import datetime, date, time
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError
from src.imports.dynamodb_helper import get_table
import boto3

private_parking_router = APIRouter(prefix="/private-parking", tags=["Private Parking"])

# Directory for saving uploaded images
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# DynamoDB and SNS
RESERVATIONS_TABLE = "Reservations"
USERS_TABLE = "Users"
dynamodb = boto3.resource("dynamodb", region_name="eu-north-1")
sns_client = boto3.client("sns", region_name="eu-north-1")


def time_str_to_obj(t_str: str) -> time:
    """Convert DynamoDB hour_range string to time object."""
    try:
        return datetime.strptime(t_str, "%H:%M:%S").time()
    except ValueError as e:
        raise


def is_now_in_range(start: time, end: time) -> bool:
    """Check if the current time is within the start-end range."""
    now = datetime.now().time()
    return start <= now <= end


@private_parking_router.post("/upload/")
async def upload_parking_image(
    file: UploadFile,
    plate: str = Form(...),
    spot_id: str = Form(default="1")
):
    """
    Upload a parking image, check current reservation,
    and send SMS if the detected plate does not match the reservation.
    """
    try:
        # --- File validation ---
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
            
        if not file.filename.lower().endswith((".jpg", ".jpeg", ".png")):
            raise HTTPException(status_code=400, detail="Invalid file type")

        # --- Normalize plate ---
        plate = plate.strip().upper() if plate else ""

        # --- Save image locally ---
        safe_filename = file.filename.replace(' ', '_').replace('/', '_')
        save_path = UPLOAD_DIR / f"spot_{spot_id}_{safe_filename}"
        
        try:
            with save_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(status_code=500, detail="Failed to save image")

        # --- Check reservations ---
        reservations_table = get_table(RESERVATIONS_TABLE)
        users_table = get_table(USERS_TABLE)
        today_str = date.today().isoformat()

        try:
            # Scan for all reservations today
            response = reservations_table.scan(
                FilterExpression=Attr("date").eq(today_str)
            )
            reservations = response.get("Items", [])

            active_reservation = None
            plate_matches = None
            alert_sent = False
            current_time = datetime.now().time()

            for reservation in reservations:
                try:
                    # Check different possible formats for hour_range
                    hour_range = reservation.get("hour_range", [])
                    
                    # Handle different DynamoDB formats
                    if isinstance(hour_range, dict):
                        if 'L' in hour_range:
                            hour_range = [item.get('S', item) for item in hour_range['L']]
                        else:
                            continue
                    
                    if not isinstance(hour_range, list) or len(hour_range) < 2:
                        continue
                    
                    # Extract start and end times
                    start_str = hour_range[0]
                    end_str = hour_range[1]
                    
                    # Handle nested dict structure if needed
                    if isinstance(start_str, dict):
                        start_str = start_str.get('S', start_str)
                    if isinstance(end_str, dict):
                        end_str = end_str.get('S', end_str)
                        
                    start_time = time_str_to_obj(start_str)
                    end_time = time_str_to_obj(end_str)

                    if is_now_in_range(start_time, end_time):
                        active_reservation = reservation
                        
                        # Get reserved plate - handle different formats
                        car_plate_raw = reservation.get("car_plate", "")
                        if isinstance(car_plate_raw, dict):
                            car_plate_raw = car_plate_raw.get('S', '')
                        
                        reserved_plate = str(car_plate_raw).strip().upper()

                        if reserved_plate == plate:
                            plate_matches = True
                        else:
                            plate_matches = False
                            
                            # Get user email - handle different formats
                            user_email_raw = reservation.get("email", "")
                            if isinstance(user_email_raw, dict):
                                user_email_raw = user_email_raw.get('S', '')
                            user_email = str(user_email_raw).strip()
                            
                            if user_email:
                                try:
                                    user_response = users_table.get_item(Key={"email": user_email})
                                    user_item = user_response.get("Item")
                                    
                                    if user_item:
                                        # Get phone number - handle different formats
                                        phone_raw = user_item.get("phone", "")
                                        if isinstance(phone_raw, dict):
                                            phone_raw = phone_raw.get('S', '')
                                        phone_number = str(phone_raw).strip()
                                        
                                        # Format phone number
                                        if phone_number and not phone_number.startswith('+'):
                                            if phone_number.startswith('0'):
                                                phone_number = '+4' + phone_number[1:]
                                            else:
                                                phone_number = '+40' + phone_number
                                        
                                        if phone_number:
                                            try:
                                                message = (
                                                    f"🚨 PARKING ALERT!\n"
                                                    f"Car plate: {plate}\n"
                                                    f"Your reserved plate: {reserved_plate}\n"
                                                    f"Time: {datetime.now().strftime('%H:%M:%S')}\n"
                                                    f"Please check your parking spot."
                                                )
                                                
                                                sns_response = sns_client.publish(
                                                    PhoneNumber=phone_number,
                                                    Message=message,
                                                    MessageAttributes={
                                                        'SMS.SMSType': {
                                                            'DataType': 'String',
                                                            'StringValue': 'Transactional'
                                                        }
                                                    }
                                                )
                                                
                                                alert_sent = True
                                                
                                            except ClientError as e:
                                                pass
                                            except Exception as e:
                                                pass
                                        else:
                                            pass
                                    else:
                                        pass
                                        
                                except ClientError as e:
                                    pass
                                except Exception as e:
                                    pass
                            else:
                                pass
                        
                        break  # Only check the first active reservation
                        
                except Exception as e:
                    # Silent continue for parsing errors
                    continue
                    
            if not active_reservation:
                pass

            # Build response message
            status_message = "Image processed successfully"
            if active_reservation:
                if plate_matches:
                    status_message = "Access granted - plate matches reservation"
                else:
                    status_message = "Alert sent - unauthorized vehicle detected" if alert_sent else "Unauthorized vehicle detected"
            else:
                status_message = "No active reservation found"

            result = {
                "plate_detected": plate,
                "image_url": f"/uploads/{save_path.name}",
                "success": True,
                "status": status_message,
                "active_reservation": active_reservation,
                "plate_matches": plate_matches,
                "alert_sent": alert_sent,
                "reservations_checked": len(reservations)
            }
            
            return result

        except ClientError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {e.response['Error']['Message']}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")