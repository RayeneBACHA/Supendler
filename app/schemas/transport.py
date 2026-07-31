from enum import Enum
from pydantic import BaseModel

class TransportMode(str, Enum):
    walk = "walk"
    bike = "bike"
    scooter = "scooter"

class AvailableOptionsRequest(BaseModel):
    distance_km: float

    has_own_bike: bool = False
    has_own_scooter: bool = False

    nearby_bikes: int = 0
    nearby_scooters: int = 0

    nearest_bike_distance_m: int = 0
    nearest_scooter_distance_m: int = 0

    scooter_battery_percent: int = 0