from pydantic import BaseModel
from typing import Optional

class PrivateParking(BaseModel):
    plate_detected: Optional[str]
    image_url: Optional[str]
    success: bool
    plate_matches: Optional[bool] = None
    alert_sent: Optional[bool] = None
    reservations_checked: Optional[int] = None
