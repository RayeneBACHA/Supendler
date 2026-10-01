from app.schemas.route import(
    MobilitySegment,
    SegmentRole,
    SharedBikeAvailability,
    SharedScooterAvailability
)
from app.schemas.transport import TransportMode
from app.services.transport_service import TransportService

class MobilityOptionService:
    MAX_SHARED_VEHICLE_WALK_DISTANCE_M = 500
    MIN_SCOOTER_BATTERY_PERCENT = 20

    SHARED_BIKE_UNLOCK_MINUTES = 1.0
    SHARED_BIKE_PARK_MINUTES = 1.0

    SHARED_SCOOTER_UNLOCK_MINUTES = 1.0
    SHARED_SCOOTER_PARK_MINUTES = 1.0

    FOLD_BIKE_MINUTES = 1.0
    UNFOLD_BIKE_MINUTES = 1.0

    def __init__(self, transport_service: TransportService):
        self.transport_service = transport_service


    def generate_options(
            self,
            segment: MobilitySegment,
            segment_role: SegmentRole,
            has_folding_bike: bool
    ) -> list[dict]:
        options = []

        options.append(
            self._build_walking_option(
                segment.walk_distance_km,
                segment_role
            )
        )

        if (
            has_folding_bike
            and segment.folding_bike_distance_km is not None
        ):
            options.append(
                self._build_folding_bike_option(
                    segment.folding_bike_distance_km,
                    segment_role
                )
            )

        if self._shared_bike_is_usable(segment.shared_bike):
            options.append(
                self._build_shared_bike_option(
                    segment.shared_bike,
                    segment_role
                )
            )

        if self._shared_scooter_is_usable(segment.shared_scooter):
            options.append(
                self._build_shared_scooter_option(
                    segment.shared_scooter,
                    segment_role
                )
            )

        return sorted(
            options,
            key=lambda option: option["time_minutes"]
        )

    def _build_walking_option(
            self,
            distance_km: float,
            segment_role: SegmentRole
    ) -> dict:
        walking_time = self.transport_service.calculate_minutes(
            distance_km,
            TransportMode.walk
        )

        return {
            "segment_role": segment_role.value,
            "mode": "walk",
            "source": "always_available",
            "time_minutes": walking_time,
            "steps": [
                {
                    "action": "walk",
                    "distance_km": distance_km,
                    "time_minutes": walking_time
                }
            ]
        }

    def _build_folding_bike_option(
            self,
            distance_km: float,
            segment_role: SegmentRole
    ) -> dict:
        steps = []
        total_time = 0.0

        if segment_role == SegmentRole.egress:
            steps.append({
                "action": "unfold_bike",
                "time_minutes": self.UNFOLD_BIKE_MINUTES
            })

            total_time += self.UNFOLD_BIKE_MINUTES

        riding_time = self.transport_service.calculate_minutes(
            distance_km,
            TransportMode.bike
        )

        steps.append({
            "action": "ride_folding_bike",
            "distance_km": distance_km,
            "time_minutes": riding_time
        })

        total_time += riding_time

        if segment_role == SegmentRole.access:
            steps.append({
                "action": "fold_bike",
                "time_minutes": self.FOLD_BIKE_MINUTES
            })

            total_time += self.FOLD_BIKE_MINUTES

        return {
            "segment_role": segment_role.value,
            "mode": "bike",
            "source": "folding_bike",
            "time_minutes": round(total_time, 1),
            "steps": steps
        }

    def _shared_bike_is_usable(
        self,
        bike: SharedBikeAvailability
    ) -> bool:
        if bike.available_count <= 0 or not bike.pickup_allowed or not bike.dropoff_allowed_at_end:
            return False

        if bike.nearest_vehicle_walk_distance_m is None or bike.ride_distance_km is None:
            return False

        if (
            bike.nearest_vehicle_walk_distance_m > self.MAX_SHARED_VEHICLE_WALK_DISTANCE_M
        ):
            return False

        return True


    def _build_shared_bike_option(
        self,
        bike: SharedBikeAvailability,
        segment_role: SegmentRole
    ) -> dict:
        walk_distance_km = (
            bike.nearest_vehicle_walk_distance_m / 1000
        )

        walking_time = self.transport_service.calculate_minutes(
            walk_distance_km,
            TransportMode.walk
        )

        riding_time = self.transport_service.calculate_minutes(
            bike.ride_distance_km,
            TransportMode.bike
        )

        total_time = (
            walking_time
            + self.SHARED_BIKE_UNLOCK_MINUTES
            + riding_time
            + self.SHARED_BIKE_PARK_MINUTES
        )

        return {
            "segment_role": segment_role.value,
            "mode": "bike",
            "source": "shared_bike",
            "available_count": bike.available_count,
            "time_minutes": round(total_time, 1),
            "steps": [
                {
                    "action": "walk_to_shared_bike",
                    "distance_km": walk_distance_km,
                    "time_minutes": walking_time
                },
                {
                    "action": "unlock_shared_bike",
                    "time_minutes": self.SHARED_BIKE_UNLOCK_MINUTES
                },
                {
                    "action": "ride_shared_bike",
                    "distance_km": bike.ride_distance_km,
                    "time_minutes": riding_time
                },
                {
                    "action": "park_shared_bike",
                    "time_minutes": self.SHARED_BIKE_PARK_MINUTES
                }
            ]
        }


    def _shared_scooter_is_usable(
        self,
        scooter: SharedScooterAvailability
    ) -> bool:
        if scooter.available_count <= 0:
            return False

        if not scooter.pickup_allowed:
            return False

        if not scooter.dropoff_allowed_at_end:
            return False

        if scooter.nearest_vehicle_walk_distance_m is None:
            return False

        if scooter.ride_distance_km is None:
            return False

        if scooter.battery_percent is None:
            return False

        if (
            scooter.nearest_vehicle_walk_distance_m
            > self.MAX_SHARED_VEHICLE_WALK_DISTANCE_M
        ):
            return False

        if (
            scooter.battery_percent
            < self.MIN_SCOOTER_BATTERY_PERCENT
        ):
            return False

        return True

    
    def _build_shared_scooter_option(
        self,
        scooter: SharedScooterAvailability,
        segment_role: SegmentRole
    ) -> dict:
        walk_distance_km = (
            scooter.nearest_vehicle_walk_distance_m / 1000
        )

        walking_time = self.transport_service.calculate_minutes(
            walk_distance_km,
            TransportMode.walk
        )

        riding_time = self.transport_service.calculate_minutes(
            scooter.ride_distance_km,
            TransportMode.scooter
        )

        total_time = (
            walking_time
            + self.SHARED_SCOOTER_UNLOCK_MINUTES
            + riding_time
            + self.SHARED_SCOOTER_PARK_MINUTES
        )

        return {
            "segment_role": segment_role.value,
            "mode": "scooter",
            "source": "shared_scooter",
            "available_count": scooter.available_count,
            "battery_percent": scooter.battery_percent,
            "time_minutes": round(total_time, 1),
            "steps": [
                {
                    "action": "walk_to_shared_scooter",
                    "distance_km": walk_distance_km,
                    "time_minutes": walking_time
                },
                {
                    "action": "unlock_shared_scooter",
                    "time_minutes": self.SHARED_SCOOTER_UNLOCK_MINUTES
                },
                {
                    "action": "ride_shared_scooter",
                    "distance_km": scooter.ride_distance_km,
                    "time_minutes": riding_time
                },
                {
                    "action": "park_shared_scooter",
                    "time_minutes": self.SHARED_SCOOTER_PARK_MINUTES
                }
            ]
        }

