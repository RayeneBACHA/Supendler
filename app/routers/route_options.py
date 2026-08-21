from fastapi import APIRouter, HTTPException

from app.data.fake_db import routes, stops, trips, stop_times
from app.schemas.route import RouteOptionsRequest
from app.services.mobility_option_service import MobilityOptionService
from app.services.public_transport_service import PublicTransportService
from app.services.route_service import RouteService
from app.services.transport_service import TransportService
from app.schemas.route_response import RouteOptionsResponse
from app.services.time_service import TimeService

router = APIRouter(tags=["route options"])
transport_service = TransportService()
time_service = TimeService()

mobility_option_service = MobilityOptionService(
    transport_service=transport_service
)

public_transport_service = PublicTransportService(
    stops=stops,
    routes=routes,
    trips=trips,
    stop_times=stop_times,
    time_service=time_service
)

route_service = RouteService(
    mobility_option_service=mobility_option_service,
    public_transport_service=public_transport_service
)


@router.post(
    "/route_options",
    response_model=RouteOptionsResponse
)
def get_route_options(request: RouteOptionsRequest):
    
    start_stop = public_transport_service.get_stop_by_id(
        request.station_pair.start_station_id
    )

    if start_stop is None:
        raise HTTPException(
            status_code=404,
            detail="Start stop not found"
        )

    end_stop = public_transport_service.get_stop_by_id(
            request.station_pair.end_station_id
        )
    
    if end_stop is None:
        raise HTTPException(
            status_code=404,
            detail="End stop not found"
        )

    result = route_service.generate_route_options(request)

    return {
        "start_stop": {
            "id": start_stop["stop_id"],
            "name": start_stop["stop_name"],
            "city": start_stop["city"]
        },

        "end_stop": {
            "id": end_stop["stop_id"],
            "name": end_stop["stop_name"],
            "city": end_stop["city"]
        },

        **result
    }