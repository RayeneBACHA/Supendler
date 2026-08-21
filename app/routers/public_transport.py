from fastapi import APIRouter, HTTPException
from app.services.time_service import TimeService

from app.data.fake_db import stops, routes, trips, stop_times
from app.services.public_transport_service import PublicTransportService

router = APIRouter(tags=["public transport"])

time_service = TimeService()

public_transport_service = PublicTransportService(
    stops=stops,
    routes=routes,
    trips=trips,
    stop_times=stop_times,
    time_service=time_service
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


@router.get("/stops/{stop_id}/trips")
def get_trips_for_stop(stop_id: int):
    stop = public_transport_service.get_stop_by_id(stop_id)

    if stop is None:
        raise HTTPException(status_code=404, detail="Stop not found")

    return {
        "stop": stop,
        "trips": public_transport_service.get_trips_for_stop(stop_id)
    }