from pydantic import BaseModel, Field, model_validator
from enum import Enum

class SegmentRole(str, Enum):
    direct = "direct"
    access = "access"
    egress = "egress"

class StopPair(BaseModel):
    start_stop_id: int = Field(gt=0)
    end_stop_id: int = Field(gt=0)

    @model_validator(mode="after")
    def stops_must_be_different(self):
        if self.start_stop_id == self.end_stop_id:
            raise ValueError("Start stop and end stop must be different")

        return self


class UserMobility(BaseModel):
    has_folding_bike: bool = False


class SharedBikeAvailability(BaseModel):
    available_count: int = Field(default=0, ge=0)

    nearest_vehicle_walk_distance_m: int | None = Field(
        default=None,
        ge=0
    )

    ride_distance_km: float | None = Field(
        default=None,
        ge=0
    )

    pickup_allowed: bool = True
    dropoff_allowed_at_end: bool = False

    @model_validator(mode="after")
    def validate_available_bike_data(self):
        if self.available_count > 0:
            if self.nearest_vehicle_walk_distance_m is None:
                raise ValueError(
                    "Walking distance to the nearest shared bike is required"
                )

            if self.ride_distance_km is None:
                raise ValueError(
                    "shared_bike ride distance is required"
                )

        return self


class SharedScooterAvailability(BaseModel):
    available_count: int = Field(default=0, ge=0)

    nearest_vehicle_walk_distance_m: int | None = Field(
        default=None,
        ge=0
    )

    ride_distance_km: float | None = Field(
        default=None,
        ge=0
    )

    battery_percent: int | None = Field(
        default=None,
        ge=0,
        le=100
    )

    pickup_allowed: bool = True
    dropoff_allowed_at_end: bool = False

    @model_validator(mode="after")
    def validate_available_scooter_data(self):
        if self.available_count > 0:
            if self.nearest_vehicle_walk_distance_m is None:
                raise ValueError(
                    "Walking distance to the nearest shared scooter is required"
                )

            if self.ride_distance_km is None:
                raise ValueError(
                    "Shared-scooter ride distance is required"
                )

            if self.battery_percent is None:
                raise ValueError(
                    "Scooter battery percentage is required"
                )

        return self


class MobilitySegment(BaseModel):
    walk_distance_km: float = Field(ge=0)

    folding_bike_distance_km: float | None = Field(
        default=None,
        ge=0
    )

    shared_bike: SharedBikeAvailability = Field(
        default_factory=SharedBikeAvailability
    )

    shared_scooter: SharedScooterAvailability = Field(
        default_factory=SharedScooterAvailability
    )


class JourneyTime(BaseModel):
    """
    Describes when the user is ready to start the journey.
    """

    ready_time: str

    @model_validator(mode="after")
    def validate_departure_time(self):
        try:
            hours, minutes = map(
                int,
                self.ready_time.split(":")
            )
        except ValueError:
            raise ValueError(
                "ready_time must use HH:MM format"
            )

        if not 0 <= hours <= 23:
            raise ValueError(
                "Hour must be between 00 and 23"
            )

        if not 0 <= minutes <= 59:
            raise ValueError(
                "Minute must be between 00 and 59"
            )

        return self


    
class RouteOptionsRequest(BaseModel):
    journey: JourneyTime

    stop_pair: StopPair
    user: UserMobility

    direct: MobilitySegment
    access: MobilitySegment
    egress: MobilitySegment

    @model_validator(mode="after")
    def validate_folding_bike_distances(self):

        if self.user.has_folding_bike:

            if self.direct.folding_bike_distance_km is None:
                raise ValueError(
                    "direct folding bike distance is required"
                    "when has_folding_bike is true"
                )

            if self.access.folding_bike_distance_km is None:
                            raise ValueError(
                                "access folding bike distance is required"
                                "when has_folding_bike is true"
                            )

            if self.egress.folding_bike_distance_km is None:
                            raise ValueError(
                                "egress folding bike distance is required"
                                "when has_folding_bike is true"
                            )

        return self


    @model_validator(mode="after")
    def validate_walk_distances(self):

        if self.direct.walk_distance_km is None:
            raise ValueError(
                "direct walk distance is required"
            )

        if self.access.walk_distance_km is None:
            raise ValueError(
                "access walk distance is required"
            )

        if self.egress.walk_distance_km is None:
            raise ValueError(
                    "egress walk distance is required"
            )

        return self