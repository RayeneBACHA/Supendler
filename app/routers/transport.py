from fastapi import APIRouter, HTTPException

from app.schemas.transport import TransportMode, AvailableOptionsRequest
from app.services.transport_service import TransportService

router = APIRouter(tags=["transport"])

transport_service = TransportService()

@router.get("/travel-time")
def calculate_travel_time(distance_km: float, mode: TransportMode):
    if distance_km <= 0:
        raise HTTPException(status_code=400, detail="Distance must be greater than 0")
    
    speed = transport_service.get_speed(mode);
    time_minutes = transport_service.calculate_minutes(distance_km, mode)

    return {
        "distance_km": distance_km,
        "mode": mode.value,
        "speed_kmh": speed,
        "time_minutes": time_minutes
    }

@router.post("/available_options")
def get_available_options(request: AvailableOptionsRequest):
    if request.distance_km <= 0:
        raise HTTPException(status_code=400, detail="Distance must be greater than 0")
    
    return transport_service.get_available_options(request)