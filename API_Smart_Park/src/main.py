from fastapi import FastAPI, HTTPException

from src.routers.register_router import register_router, login_router
from src.routers.car_plate_router import car_plate_router
from src.routers.reservation_router import reservation_router
from src.routers.profile_router import profile_router
from src.routers.private_park_router import private_parking_router

app = FastAPI()

# Include all routers
app.include_router(register_router)
app.include_router(login_router)
app.include_router(reservation_router)
app.include_router(car_plate_router)
app.include_router(profile_router)
app.include_router(private_parking_router)


@app.get("/")
def read_root():
    return {"message": "Parking System API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)