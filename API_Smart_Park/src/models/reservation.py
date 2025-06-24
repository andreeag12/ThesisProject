from pydantic import BaseModel, EmailStr, validator
from datetime import date, time
from typing import List, Optional

class Reservation(BaseModel):
    email: EmailStr
    car_plate: str
    parking_spot_id: int
    date: date
    hour_range: List[time]  # expects two times: start and end
    status: Optional[str] = "pending"

    @validator('hour_range', pre=True)
    def parse_hour_range(cls, v):
        if isinstance(v, list):
            # Convert strings to time objects if needed
            return [time.fromisoformat(t) if isinstance(t, str) else t for t in v]
        raise ValueError('hour_range must be a list of two times')
