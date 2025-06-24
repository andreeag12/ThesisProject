from pydantic import BaseModel

class ParkingSpot(BaseModel):
    spot_id: str
    floor: str