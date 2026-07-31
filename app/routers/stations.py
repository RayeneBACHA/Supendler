from fastapi import APIRouter, HTTPException

from app.data.fake_db import stations
from app.schemas.station import Station
from app.services.station_service import StationService

router = APIRouter(tags=["stations"])

station_service = StationService(stations)


@router.get("/stations")
def get_stations():
    return station_service.get_all()

@router.post("/stations")
def create_station(new_station: Station):
    return station_service.create(new_station)

@router.get("/stations/{station_id}")
def get_station(station_id: int):
    station = station_service.get_by_id(station_id)

    if station == None:
        raise HTTPException(status_code=404, detail="Station not found")
    
    return station

@router.put("/stations/{station_id}")
def update_station(station_id: int, updated_station: Station):
    station = station_service.update(station_id, updated_station)

    if station is None:
        raise HTTPException(status_code=404, detail="Station not found")
    
    return station

@router.delete("/stations/{station_id}")
def delete_station(station_id: int):
    station = station_service.delete(station_id)

    if station is None:
        raise HTTPException(status_code= 404, detail="Station not found")
    
    return {
        "message": "Station deleted",
        "station": station
    }