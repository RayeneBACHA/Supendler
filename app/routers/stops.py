from fastapi import APIRouter, HTTPException

from app.data.fake_db import stops
from app.schemas.stop import Stop
from app.services.stop_service import StopService

router = APIRouter(tags=["stops"])

stop_service = StopService(stops)


@router.get("/stops")
def get_stops():
    return stop_service.get_all()

@router.post("/stops")
def create_stop(new_stop: Stop):
    return stop_service.create(new_stop)

@router.get("/stops/{stop_id}")
def get_stop(stop_id: int):
    stop = stop_service.get_by_id(stop_id)

    if stop == None:
        raise HTTPException(status_code=404, detail="Stop not found")
    
    return stop

@router.put("/stops/{stop_id}")
def update_stop(stop_id: int, updated_stop: Stop):
    stop = stop_service.update(stop_id, updated_stop)

    if stop is None:
        raise HTTPException(status_code=404, detail="Stop not found")
    
    return stop

@router.delete("/stop/{stop_id}")
def delete_stop(stop_id: int):
    stop =stop_service.delete(stop_id)

    if stop is None:
        raise HTTPException(status_code= 404, detail="Stop not found")
    
    return {
        "message": "Stop deleted",
        "stop": stop
    }