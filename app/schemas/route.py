from pydantic import BaseModel, Field, model_validator
from enum import Enum

class SegmentRole(str, Enum):
    direct = "direct"
    access = "access"
    egress = "egress"

class StationPair(BaseModel):
    start_station_id: int = Field(gt=0)
    end_station_id: int = Field(gt=0)

    @model_validator(mode="after")
    def stations_must_be_different(self):
        if self.start_station_id == self.end_station_id:
            raise ValueError("Start station and end station must be different")

        return self


class UserMobility(BaseModel):
    has_folding_bike: bool = False


class SharedBikeAvailability(BaseModel):
    available_count: int = Field(default=0, ge=0)

    nearest_vehicle_walk_distance_m: int | None = Field(
        default=0,
        ge=0
    )

    ride_distance_km: float | None = Field(
        default=0,
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


class RouteOptionsRequest(BaseModel):
    station_pair: StationPair
    user: UserMobility

    direct: MobilitySegment
    access: MobilitySegment
    egress: MobilitySegment