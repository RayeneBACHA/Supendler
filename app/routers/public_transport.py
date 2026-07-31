from fastapi import APIRouter, HTTPException

from app.data.fake_db import stations, lines, trips, trip_stops
from app.services.public_transport_service import PublicTransportService

router = APIRouter(tags=["public transport"])

public_transport_service = PublicTransportService(
    stations,
    lines,
    trips,
    trip_stops
)


@router.get("/trips")
def get_trips():
    return public_transport_service.get_all_trips()


@router.get("/trips/direct")
def get_direct_trips(from_station_id: int, to_station_id: int):
    direct_trips = public_transport_service.find_direct_trips(
        from_station_id,
        to_station_id
    )

    if len(direct_trips) == 0:
        raise HTTPException(status_code=404, detail="No direct trip found")

    return direct_trips


@router.get("/stations/{station_id}/trips")
def get_trips_for_station(station_id: int):
    station = public_transport_service.get_station_by_id(station_id)

    if station is None:
        raise HTTPException(status_code=404, detail="Station not found")

    return {
        "station": station,
        "trips": public_transport_service.get_trips_for_station(station_id)
    }