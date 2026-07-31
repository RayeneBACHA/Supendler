from fastapi import APIRouter, HTTPException

from app.data.fake_db import lines, stations, trip_stops, trips
from app.schemas.route import RouteOptionsRequest
from app.services.mobility_option_service import MobilityOptionService
from app.services.public_transport_service import PublicTransportService
from app.services.route_service import RouteService
from app.services.transport_service import TransportService


router = APIRouter(tags=["route options"])
transport_service = TransportService()

mobility_option_service = MobilityOptionService(
    transport_service=transport_service
)

public_transport_service = PublicTransportService(
    stations=stations,
    lines=lines,
    trips=trips,
    trip_stops=trip_stops
)

route_service = RouteService(
    mobility_option_service=mobility_option_service,
    public_transport_service=public_transport_service
)


@router.post("/route_options")
def get_route_options(request: RouteOptionsRequest):
    start_station = public_transport_service.get_station_by_id(
        request.station_pair.start_station_id
    )

    if start_station is None:
        raise HTTPException(
            status_code=404,
            detail="Start station not found"
        )

    end_station = public_transport_service.get_station_by_id(
            request.station_pair.end_station_id
        )
    
    if end_station is None:
        raise HTTPException(
            status_code=404,
            detail="End station not found"
        )

    result = route_service.generate_route_options(request)

    return {
        "start_station": start_station,
        "end_station": end_station,
        **result
    }