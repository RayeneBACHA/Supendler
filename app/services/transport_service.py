from app.schemas.transport import TransportMode, AvailableOptionsRequest

class TransportService:
    SPEED_KMH = {
        "walk": 5,
        "bike": 15,
        "scooter": 20
    }

    MAX_SHARED_VEHICLE_DISTANCE =  500
    MIN_SCOOTER_BATTERY_PERCENT = 20

    def calculate_minutes(self, distance_km: float, mode: TransportMode):
        speed = self.get_speed(mode)
        time_minutes = (distance_km / speed) * 60
        return round(time_minutes, 1)
    
    def get_speed(self, mode: TransportMode):
        return self.SPEED_KMH[mode.value]
    
    def meters_to_km(self, distance_m):
        return distance_m / 1000
    
    def calculate_shared_vehicle_time(
        self,
        trip_distance_km: float,
        distance_to_vehicle_m: float,
        mode: TransportMode
    ):
        walk_to_vehicle_km = self.meters_to_km(distance_to_vehicle_m)

        walk_time = self.calculate_minutes(
            walk_to_vehicle_km,
            TransportMode.walk
        )

        ride_time = self.calculate_minutes(
            trip_distance_km,
            mode
        )

        total_time = walk_time + ride_time

        return {
            "walk_to_vehicle_minutes": walk_time,
            "ride_minutes": ride_time,
            "time_minutes": round(total_time, 1)
        }
    def get_available_options(self, request: AvailableOptionsRequest):
        usable_options = []

        usable_options.append({
            "mode": "walk",
            "source": "always_available",
            "time_minutes": self.calculate_minutes(request.distance_km, TransportMode.walk)
        })

        if request.has_own_bike:
            usable_options.append({
            "mode": "bike",
            "source": "owned",
            "time_minutes": self.calculate_minutes(request.distance_km, TransportMode.bike)
            })
        elif request.nearby_bikes > 0 and request.nearest_bike_distance_m <= self.MAX_SHARED_VEHICLE_DISTANCE:
            shared_bike_time = self.calculate_shared_vehicle_time(
                request.distance_km,
                request.nearest_bike_distance_m,
                TransportMode.bike
            )
            
            usable_options.append({
            "mode": "bike",
            "source": "shared",
            "distance_to_vehicle_m": request.nearest_bike_distance_m,
            "walk_to_vehicle_minutes": shared_bike_time["walk_to_vehicle_minutes"],
            "ride_minutes": shared_bike_time["ride_minutes"],
            "time_minutes": shared_bike_time["time_minutes"]
        })
            
        if request.has_own_scooter:
            usable_options.append({
            "mode": "scooter",
            "source": "owned",
            "time_minutes": self.calculate_minutes(request.distance_km, TransportMode.scooter)
        })
        elif (
            request.nearby_scooters > 0
            and request.nearest_scooter_distance_m <= self.MAX_SHARED_VEHICLE_DISTANCE
            and request.scooter_battery_percent >= self.MIN_SCOOTER_BATTERY_PERCENT
        ) :
            shared_scooter_time = self.calculate_shared_vehicle_time(
                request.distance_km, 
                request.nearest_scooter_distance_m, 
                TransportMode.scooter
            )


            usable_options.append({
            "mode": "scooter",
            "source": "shared",
            "distance_to_vehicle_m": request.nearest_scooter_distance_m,
            "battery_percent": request.scooter_battery_percent,
            "walk_to_vehicle_minutes": shared_scooter_time["walk_to_vehicle_minutes"],
            "ride_minutes": shared_scooter_time["ride_minutes"],
            "time_minutes": shared_scooter_time["time_minutes"]
        })
        
        recommended_option = min(
            usable_options,
            key=lambda option: option["time_minutes"]
        )

        return {
            "distance_km" : request.distance_km,
            "usable_options": usable_options,
            "recommended_option": recommended_option
        }
        