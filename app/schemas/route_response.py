from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.route import SegmentRole
from app.schemas.station import StationResponse
from app.schemas.transport import TransportMode

from enum import Enum

class MobilityAction(BaseModel):
    action: str

    time_minutes: float = Field(ge=0)

    distance_km: float | None = Field(
        default=None,
        ge=0
    )

class MobilityLeg(BaseModel):
    leg_type: Literal["mobility"] = "mobility"

    role: SegmentRole
    mode: TransportMode
    source: str

    time_minutes: float = Field(ge=0)

    actions: list[MobilityAction]


class PublicTransportStop(BaseModel):
    station_id: int
    station_name: str

    stop_order: int = Field(gt=0)
    minute: int = Field(ge=0)

    #Scheduled clock time at this stop
    scheduled_time: str


class PublicTransportLeg(BaseModel):
    leg_type: Literal["public_transport"] = "public_transport"

    trip_id: int
    line: str
    line_type: str
    destination: str

    # Actual scheduled times for this section of the trip.
    departure_time: str
    arrival_time: str

    duration_minutes: float = Field(ge=0)
    stops: list[PublicTransportStop]

class RouteProfile(str, Enum):
    direct_walk = "direct_walk"
    direct_bike = "direct_bike"
    direct_shared = "direct_shared"

    pt_walk = "pt_walk"
    pt_folding_bike = "pt_folding_bike"
    pt_shared = "pt_shared"

class RouteOption(BaseModel):
    route_type: Literal[
        "direct",
        "public_transport_combo"
    ]

    profile: RouteProfile

    total_time_minutes: float = Field(ge=0)
    modes: list[str]

    # Only relevant for timetable-dependent routes.
    # Direct walk/bike/scooter routes can leave these as None.
    leave_by_time: str | None = None
    wait_before_start_minutes: float | None = Field(
        default= None,
        ge=0
    )

    # This can contain values such as "unlocks_connection" or "saves_walking_time".
    benefit: str | None = None
    

    legs: list[
        MobilityLeg | PublicTransportLeg
    ]

class RouteOptionsResponse(BaseModel):
    start_station: StationResponse
    end_station: StationResponse

    option_count: int = Field(ge=1)

    fastest_option: RouteOption
    options: list[RouteOption]