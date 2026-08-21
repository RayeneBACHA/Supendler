from app.services.time_service import TimeService

class PublicTransportService:
    def __init__(
        self,
        stops: list[dict],
        routes: list[dict],
        trips: list[dict],
        stop_times: list[dict],
        time_service: TimeService
    ):
        self.stops = stops
        self.routes = routes
        self.trips = trips
        self.stop_times = stop_times
        self.time_service = time_service

    def get_all_trips(self):
        return self.trips

    def get_stop_by_id(
        self,
        stop_id: int
    ) -> dict | None:
        for stop in self.stops:
            if stop["stop_id"] == stop_id:
                return stop

        return None

    def get_route_by_id(
        self,
        route_id: int
    ) -> dict | None:

        for route in self.routes:
            if route["route_id"] == route_id:
                return route

        return None

    def get_trip_by_id(
        self,
        trip_id: int
    ) -> dict | None:
        for trip in self.trips:
            if trip["trip_id"] == trip_id:
                return trip

        return None
    
    def get_stop_times_for_trip(
        self,
        trip_id: int
    ) -> list[dict]:

        stop_times = []

        for stop_time in self.stop_times:
            if stop_time["trip_id"] == trip_id:
                stop_times.append(stop_time)

        return sorted(
            stop_times,
            key=lambda stop_time: stop_time["stop_sequence"]
        )

    def get_trips_for_stop(
        self,
        stop_id: int
    ) -> list[dict]:
        """
        Return all scheduled trips that serve a given stop.
        """

        result = []

        for stop_time in self.stop_times:
            if stop_time["stop_id"] != stop_id:
                continue

            trip = self.get_trip_by_id(
                stop_time["trip_id"]
            )

            route = self.get_route_by_id(
                trip["route_id"]
            )

            result.append({
                "trip_id": trip["trip_id"],
                "route": route["route_short_name"],
                "route_type": route["route_type"],
                "destination": trip["trip_headsign"],
                "stop_sequence": stop_time["stop_sequence"],
                "arrival_time": stop_time["arrival_time"],
                "departure_time": stop_time["departure_time"]
            })

        return result

    def find_direct_trips(
        self,
        from_stop_id: int,
        to_stop_id: int
    ) -> list[dict]:

        direct_trips = []

        for trip in self.trips:

            stop_times = self.get_stop_times_for_trip(
                trip["trip_id"]
            )

            from_stop_time = None
            to_stop_time = None

            for stop_time in stop_times:

                if stop_time["stop_id"] == from_stop_id:
                    from_stop_time = stop_time

                if stop_time["stop_id"] == to_stop_id:
                    to_stop_time = stop_time

        # The trip must serve both requested stops.
            if (
                from_stop_time is None
                or to_stop_time is None
            ):
                continue

            # Origin must come before destination.
            if (
                from_stop_time["stop_sequence"]
                >= to_stop_time["stop_sequence"]
            ):
                continue

            route = self.get_route_by_id(
                trip["route_id"]
            )

            # Temporary compatibility with old API response.
            # GTFS stop_times are now the real source of truth.
            trip_start_minutes = (
                self.time_service.time_to_minutes(
                    stop_times[0]["departure_time"]
                )
            )

            stops_between = []

            for stop_time in stop_times:

                if (
                    from_stop_time["stop_sequence"]
                    <= stop_time["stop_sequence"]
                    <= to_stop_time["stop_sequence"]
                ):

                    stop = self.get_stop_by_id(
                        stop_time["stop_id"]
                    )

                    current_stop_minutes = (
                        self.time_service.time_to_minutes(
                            stop_time["departure_time"]
                        )
                    )

                    minute = (
                        current_stop_minutes
                        - trip_start_minutes
                    )

                    stops_between.append({
                        "station_id": stop["stop_id"],
                        "station_name": stop["stop_name"],
                        "stop_order": stop_time["stop_sequence"],
                        "minute": minute,
                        "scheduled_time": stop_time["departure_time"]
                    })

            departure_time = (
                from_stop_time["departure_time"]
            )

            arrival_time = (
                to_stop_time["arrival_time"]
            )

            departure_minutes = (
                self.time_service.time_to_minutes(
                    departure_time
                )
            )

            arrival_minutes = (
                self.time_service.time_to_minutes(
                    arrival_time
                )
            )

            duration_minutes = (
                arrival_minutes
                - departure_minutes
            )

            direct_trips.append({
                "trip_id": trip["trip_id"],

                "line": route["route_short_name"],
                "line_type": route["route_type"],

                "destination": trip["trip_headsign"],

                "departure_time": departure_time,
                "arrival_time": arrival_time,

                "duration_minutes": duration_minutes,

                "stops": stops_between
            })

        return direct_trips


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

    def find_unlocked_direct_trips(
        self,
        from_station_id: int,
        to_station_id: int,
        ready_time: str,
        baseline_travel_time_minutes: float,
        alternative_travel_time_minutes: float,
        baseline_safety_buffer_minutes: float = 0,
        alternative_safety_buffer_minutes: float = 0
    ) -> list[dict]:
        """
        Find public transport trips that are impossible to catch
        with the baseline mobility option but become catchable with
        the alternative mobility option.

        Walking will normally be used as the baseline.
        """

        baseline_evaluation = self.evaluate_direct_trip_access(
            from_station_id=from_station_id,
            to_station_id=to_station_id,
            ready_time=ready_time,
            travel_time_minutes=baseline_travel_time_minutes,
            safety_buffer_minutes=baseline_safety_buffer_minutes
        )

        alternative_evaluation = self.evaluate_direct_trip_access(
            from_station_id=from_station_id,
            to_station_id=to_station_id,
            ready_time=ready_time,
            travel_time_minutes=alternative_travel_time_minutes,
            safety_buffer_minutes=alternative_safety_buffer_minutes
        )

        # Index the baseline results by trip ID so we can compare
        # the same scheduled journey between both mobility options.
        baseline_by_trip_id = {
            trip["trip_id"]: trip
            for trip in baseline_evaluation
        }

        unlocked_trips = []

        for alternative_trip in alternative_evaluation:
            baseline_trip = baseline_by_trip_id[
                alternative_trip["trip_id"]
            ]

            if (
                not baseline_trip["catchable"]
                and alternative_trip["catchable"]
            ):
                unlocked_trips.append({
                    **alternative_trip,

                    "unlocks_connection": True,

                    "baseline_access": {
                        "catchable": baseline_trip["catchable"],
                        "leave_by_time": baseline_trip["leave_by_time"],
                        "wait_before_start_minutes":
                            baseline_trip["wait_before_start_minutes"]
                    }
                })

        return unlocked_trips