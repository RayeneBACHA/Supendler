from app.services.time_service import TimeService

class PublicTransportService:
    def __init__(
        self,
        stations: list[dict],
        lines: list[dict],
        trips: list[dict],
        trip_stops: list[dict],
        time_service: TimeService
    ):
        self.stations = stations
        self.lines = lines
        self.trips = trips
        self.trip_stops = trip_stops
        self.time_service = time_service

    def get_all_trips(self):
        return self.trips

    def get_station_by_id(self, station_id: int):
        for station in self.stations:
            if station["id"] == station_id:
                return station

        return None

    def get_line_by_name(self, line_name: str):
        for line in self.lines:
            if line["name"] == line_name:
                return line

        return None

    def get_trip_by_id(self, trip_id: int):
        for trip in self.trips:
            if trip["id"] == trip_id:
                return trip

        return None

    def get_stops_for_trip(self, trip_id: int):
        stops = []

        for stop in self.trip_stops:
            if stop["trip_id"] == trip_id:
                stops.append(stop)

        return sorted(stops, key=lambda stop: stop["stop_order"])

    def get_trips_for_station(self, station_id: int):
        result = []

        for stop in self.trip_stops:
            if stop["station_id"] == station_id:
                trip = self.get_trip_by_id(stop["trip_id"])
                line = self.get_line_by_name(trip["line_name"])

                result.append({
                    "trip_id": trip["id"],
                    "line": line["name"],
                    "line_type": line["type"],
                    "destination": trip["destination"],
                    "stop_order": stop["stop_order"],
                    "minute": stop["minute"]
                })

        return result

    def find_direct_trips(self, from_station_id: int, to_station_id: int):
        direct_trips = []

        for trip in self.trips:
            stops = self.get_stops_for_trip(trip["id"])

            from_stop = None
            to_stop = None

            for stop in stops:
                if stop["station_id"] == from_station_id:
                    from_stop = stop

                if stop["station_id"] == to_station_id:
                    to_stop = stop

            if from_stop is None or to_stop is None:
                continue

            if from_stop["stop_order"] >= to_stop["stop_order"]:
                continue

            departure_time = self.get_stop_time(
                trip,
                from_stop
            )

            arrival_time = self.get_stop_time(
                trip,
                to_stop
            )

            line = self.get_line_by_name(trip["line_name"])

            stops_between = []

            for stop in stops:
                if from_stop["stop_order"] <= stop["stop_order"] <= to_stop["stop_order"]:
                    station = self.get_station_by_id(stop["station_id"])

                    stops_between.append({
                        "station_id": station["id"],
                        "station_name": station["name"],
                        "stop_order": stop["stop_order"],
                        "minute": stop["minute"],
                        "scheduled_time": self.get_stop_time(
                            trip,
                            stop
                        )
                    })

            duration_minutes = to_stop["minute"] - from_stop["minute"]

            direct_trips.append({
                "trip_id": trip["id"],
                "line": line["name"],
                "line_type": line["type"],
                "destination": trip["destination"],

                "departure_time": departure_time,
                "arrival_time": arrival_time,


                "duration_minutes": duration_minutes,
                "stops": stops_between
            })

        return direct_trips

    def get_stop_time(
            self,
            trip: dict,
            stop: dict
    ) -> str:
        """
        Calculate the scheduled clock time at a specific stop.

        Each stop stores its time as an offset in minutes from the
        beginning of the trip.
        """

        trip_start_minutes = self.time_service.time_to_minutes(
            trip["start_time"]
        )

        stop_time_minutes = (
            trip_start_minutes
            + stop["minute"]
        )

        return self.time_service.minutes_to_time(
            stop_time_minutes
        )

    def can_catch_departure(
            self,
            ready_time: str,
            travel_time_minutes: float,
            departure_time: str,
            safety_buffer_minutes: float = 0
    ) -> bool:
        """
        Check whether a user can reach a departure point
        early enough to catch the scheduled public transport trip.

        The safety buffer can later be increased for modes with 
        more uncertainty, such as shared mobility 
        """

        ready_minutes = self.time_service.time_to_minutes(
            ready_time
        )

        departure_minutes = self.time_service.time_to_minutes(
            departure_time
        )

        arrival_at_station = (
            ready_minutes
            +travel_time_minutes
        )

        # The user must arrive before the latest safe arrival time,
        # not merely before the vehicle has already departed.
        latest_safe_arrival = (
            departure_minutes
            - safety_buffer_minutes
        )

        return arrival_at_station <= latest_safe_arrival


    def find_catchable_direct_trips(
            self,
            from_station_id: int,
            to_station_id: int,
            ready_time: str,
            travel_time_minutes: float,
            safety_buffer_minutes: float = 0
    ) -> list[dict]:
        """
        Return only the direct public transport trips that the user
        can actually reach before their scheduled departure.
        """

        direct_trips = self.find_direct_trips(
            from_station_id,
            to_station_id
        )

        catchable_trips = []

        for trip in direct_trips:
            if self.can_catch_departure(
                ready_time=ready_time,
                travel_time_minutes=travel_time_minutes,
                departure_time=trip["departure_time"],
                safety_buffer_minutes=safety_buffer_minutes
            ):
                catchable_trips.append(trip)

        return catchable_trips

    def evaluate_direct_trip_access(
        self,
        from_station_id: int,
        to_station_id: int,
        ready_time: str,
        travel_time_minutes: float,
        safety_buffer_minutes: float = 0
    ) -> list[dict]:
        """
        Evaluate how a ground mobility option can reach direct
        public transport trip.

        The result keeps both cachable and missed trips so that other
        routing logic can later compare mobility options.
        """

        direct_trips = self.find_direct_trips(
            from_station_id,
            to_station_id
        )

        evaluated_trips = []

        for trip in direct_trips:

            catchable = self.can_catch_departure(
                ready_time=ready_time,
                travel_time_minutes=travel_time_minutes,
                departure_time=trip["departure_time"],
                safety_buffer_minutes=safety_buffer_minutes
            )

            leave_by_time = self.time_service.calculate_leave_by_time(
                departure_time=trip["departure_time"],
                travel_time_minutes=travel_time_minutes,
                safety_buffer_minutes=safety_buffer_minutes
            )

            ready_minutes = self.time_service.time_to_minutes(
                ready_time
            )

            leave_by_minutes = self.time_service.time_to_minutes(
                leave_by_time
            )

            wait_before_start_minutes = None

            if catchable:
                wait_before_start_minutes = max(
                    0,
                    leave_by_minutes - ready_minutes
                )

            evaluated_trips.append({
                **trip,

                "catchable": catchable,
                "leave_by_time": leave_by_time,
                "wait_before_start_minutes": wait_before_start_minutes
            })

        return evaluated_trips