from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.route import SegmentRole
from app.schemas.station import StationResponse
from app.schemas.transport import TransportMode

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


class PublicTransportLeg(BaseModel):
    leg_type: Literal["public_transport"] = "public_transport"

    trip_id: int
    line: str
    line_type: str
    destination: str

    duration_minutes: float = Field(ge=0)

    stops: list[PublicTransportStop]

class RouteOption(BaseModel):
    route_type: Literal[
        "direct",
        "public_transport_combo"
    ]

    total_time_minutes: float = Field(ge=0)

    modes: list[str]

    legs: list[
        MobilityLeg | PublicTransportLeg
    ]

class RouteOptionsResponse(BaseModel):
    start_station: StationResponse
    end_station: StationResponse

    option_count: int = Field(ge=1)

    fastest_option: RouteOption
    options: list[RouteOption]