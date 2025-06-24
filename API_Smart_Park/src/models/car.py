from pydantic import  BaseModel

class CarPlate(BaseModel):
    car_plate_id: str
    owner_name: str