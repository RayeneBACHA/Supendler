from app.services.time_service import TimeService

class PublicTransportService:

    SAME_STOP_TRANSFER_WALK_MINUTES = 1
    MIN_TRANSFER_ARRIVAL_GAIN_MINUTES = 5
    FOLDING_BIKE_TRANSFER_BUFFER_MINUTES = 1
    
    def __init__(
        self,
        stops: list[dict],
        routes: list[dict],
        trips: list[dict],
        stop_times: list[dict],
        transfer_links: list[dict],
        time_service: TimeService
    ):
        self.stops = stops
        self.routes = routes
        self.trips = trips
        self.stop_times = stop_times
        self.transfer_links = transfer_links
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
                        "stop_id": stop["stop_id"],
                        "stop_name": stop["stop_name"],
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

        arrival_at_stop = (
            ready_minutes
            +travel_time_minutes
        )

        # The user must arrive before the latest safe arrival time,
        # not merely before the vehicle has already departed.
        latest_safe_arrival = (
            departure_minutes
            - safety_buffer_minutes
        )

        return arrival_at_stop <= latest_safe_arrival


    def find_catchable_direct_trips(
            self,
            from_stop_id: int,
            to_stop_id: int,
            ready_time: str,
            travel_time_minutes: float,
            safety_buffer_minutes: float = 0
    ) -> list[dict]:
        """
        Return only the direct public transport trips that the user
        can actually reach before their scheduled departure.
        """

        direct_trips = self.find_direct_trips(
            from_stop_id,
            to_stop_id
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
        from_stop_id: int,
        to_stop_id: int,
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
            from_stop_id,
            to_stop_id
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
        from_stop_id: int,
        to_stop_id: int,
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
            from_stop_id=from_stop_id,
            to_stop_id=to_stop_id,
            ready_time=ready_time,
            travel_time_minutes=baseline_travel_time_minutes,
            safety_buffer_minutes=baseline_safety_buffer_minutes
        )

        alternative_evaluation = self.evaluate_direct_trip_access(
            from_stop_id=from_stop_id,
            to_stop_id=to_stop_id,
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


    def get_stop_time_for_trip_at_stop(
        self,
        trip_id: int,
        stop_id: int,
    ) -> dict | None:

        for stop_time in self.stop_times:
            if (
                stop_time["trip_id"] == trip_id
                and stop_time["stop_id"] == stop_id
            ):
                return stop_time

        return None



    def find_one_transfer_connections(
        self,
        from_stop_id: int,
        to_stop_id: int
    ) -> list[dict]:

        connections = []

        # Try every stop as a possible transfer point.

        for transfer_stop in self.stops:

            transfer_stop_id = transfer_stop["stop_id"]

            # The origin and final destination cannot be transfer stops.
            if transfer_stop_id in {
                from_stop_id,
                to_stop_id
            }:
                continue

            # Find trips that can take us:
            # origin -> transfer stop

            first_trips = self.find_direct_trips(
                from_stop_id=from_stop_id,
                to_stop_id=transfer_stop_id
            )

            # Find trips that can take us:
            # transfer stop -> destination
            second_trips = self.find_direct_trips(
                from_stop_id=transfer_stop_id,
                to_stop_id=to_stop_id
            )

            # Try every possible Trip 1 + Trip 2 combination.
            for first_trip in first_trips:

                for second_trip in second_trips:

                    # If both parts use the same trip, the passenger
                    # never changes vehicle, so this is not a transfer.
                    if first_trip["trip_id"] == second_trip["trip_id"]:
                        continue

                    # -------------------------------------------------
                    # 1. Check whether changing vehicles is worthwhile
                    # -------------------------------------------------

                    # Does Trip 1 itself continue to the final destination?
                    first_trip_at_destination = (
                        self.get_stop_time_for_trip_at_stop(
                            trip_id=first_trip["trip_id"],
                            stop_id=to_stop_id
                        )
                    )


                    # Get Trip 1's stop-time at the transfer point.
                    first_trip_at_transfer = (
                        self.get_stop_time_for_trip_at_stop(
                            trip_id=first_trip["trip_id"],
                            stop_id=transfer_stop_id
                        )
                    )

                    # If Trip 1 continues from the transfer stop
                    # to the destination, the user could simply stay
                    # on the vehicle instead of transferring.
                    if (
                        first_trip_at_destination is not None
                        and first_trip_at_transfer is not None
                        and first_trip_at_destination["stop_sequence"]
                        > first_trip_at_transfer["stop_sequence"]
                    ) :

                        stay_on_first_arrival = (
                            self.time_service.time_to_minutes(
                                first_trip_at_destination["arrival_time"]
                            )
                        )

                        transfer_route_arrival = (
                            self.time_service.time_to_minutes(
                                second_trip["arrival_time"]
                            )
                        )

                        # Positive value = transfer arrives earlier.
                        #
                        # Example:
                        # stay on Trip 1 -> 12:50
                        # transfer       -> 12:40
                        # gain           -> 10 minutes
                        transfer_gain = (
                            stay_on_first_arrival 
                            - transfer_route_arrival
                        )

                        # Do not recommend changing vehicles for only
                        # a tiny improvement.
                        if (
                            transfer_gain 
                            < self.MIN_TRANSFER_ARRIVAL_GAIN_MINUTES
                        ):
                            continue

                    # ---------------------------------------------
                    # 2. Check whether the transfer is physically possible
                    # ---------------------------------------------

                    # When does Trip 1 arrive at the transfer stop?
                    first_arrival = self.time_service.time_to_minutes(
                        first_trip["arrival_time"]
                    )

                    # When does Trip 2 leave the transfer stop?
                    second_departure = self.time_service.time_to_minutes(
                        second_trip["departure_time"]
                    )

                    # Total time available between the two vehicles.
                    total_transfer_time_minutes = (
                        second_departure
                        - first_arrival
                    )

                    if (
                        total_transfer_time_minutes 
                        < self.SAME_STOP_TRANSFER_WALK_MINUTES
                    ) :
                        continue

                    # -------------------------------------------------
                    # 3. Valid and useful transfer -> save it
                    # -------------------------------------------------

                    connections.append({
                        "first_trip": first_trip,

                        "transfer_stop": transfer_stop,

                        "transfer_from_stop": transfer_stop,
                        "transfer_to_stop": transfer_stop,

                        "second_trip":  second_trip,
                        
                        "total_transfer_time_minutes":
                            total_transfer_time_minutes,
                        "walk_transfer_time_minutes":
                            self.SAME_STOP_TRANSFER_WALK_MINUTES
                    })

        return connections

    def _find_best_normal_continuation_arrival_minutes(
        self,
        first_trip_id: int,
        from_stop_id: int,
        to_stop_id: int
    ) -> int | None:
        """
        Find the earliest arrival at the final PT stop that is possible
        without leaving the normal path of PT1.

        Starting from the user's boarding stop, inspect every upcoming
        stop of PT1 and consider:

        1. staying on PT1 if it reaches the destination;
        2. making a normal same-stop transfer to another trip.

        This result is used as the baseline when deciding whether an
        inter-stop mobility transfer provides a meaningful advantage.
        """

        origin_stop_time = self.get_stop_time_for_trip_at_stop(
            trip_id=first_trip_id,
            stop_id=from_stop_id
        )

        if origin_stop_time is None:
            return None

        stop_times = self.get_stop_times_for_trip(
            first_trip_id
        )

        best_arrival_minutes = None

        for stop_time in stop_times:

            # Only stations that come after where the user boarded PT1.
            if (
                stop_time["stop_sequence"]
                <= origin_stop_time["stop_sequence"]
            ):
                continue

            current_stop_id = stop_time["stop_id"]

            first_trip_arrival_minutes = (
                self.time_service.time_to_minutes(
                    stop_time["arrival_time"]
                )
            )

            # ---------------------------------------------------------
            # PT1 itself reaches the final PT stop.
            # ---------------------------------------------------------

            if current_stop_id == to_stop_id:

                if (
                    best_arrival_minutes is None
                    or first_trip_arrival_minutes
                    < best_arrival_minutes
                ):
                    best_arrival_minutes = first_trip_arrival_minutes

                continue

            # ---------------------------------------------------------
            # Can we leave PT1 here and take another normal PT trip
            # from THIS SAME stop to the final stop?
            # ---------------------------------------------------------

            onward_trips = self.find_direct_trips(
                from_stop_id=current_stop_id,
                to_stop_id=to_stop_id
            )

            for onward_trip in onward_trips:

                if onward_trip["trip_id"] == first_trip_id:
                    continue

                onward_departure_minutes = (
                    self.time_service.time_to_minutes(
                        onward_trip["departure_time"]
                    )
                )

                available_transfer_time = (
                    onward_departure_minutes
                    - first_trip_arrival_minutes
                )

                if (
                    available_transfer_time
                    < self.SAME_STOP_TRANSFER_WALK_MINUTES
                ):
                    continue

                onward_arrival_minutes = (
                    self.time_service.time_to_minutes(
                        onward_trip["arrival_time"]
                    )
                )

                if (
                    best_arrival_minutes is None
                    or onward_arrival_minutes
                    < best_arrival_minutes
                ):
                    best_arrival_minutes = onward_arrival_minutes

        
        return best_arrival_minutes

    def find_inter_stop_transfer_connections(
        self,
        from_stop_id: int,
        to_stop_id: int
    ) -> list[dict]:
        """
        Find PT connections that require moving between two different stops.

        Search is PT-path-first:

        1. Start with a PT trip the user can board at the origin.
        2. Inspect its upcoming stops.
        3. Determine the best normal PT continuation toward the destination.
        4. Look for transfer links from those upcoming stops to nearby stops.
        5. Find PT trips from the linked stop to the destination.
        6. Record whether walking or folding bike can make the transfer.

        The normal continuation is kept as a baseline so RouteService can
        later decide whether the mobility-assisted transfer saves enough
        final-arrival time to be worth recommending.
        """

        connections = []

        # ------------------------------------------------------------
        # Start with PT1, not with transfer links.
        # ------------------------------------------------------------
        
        first_trip_ids = {
            trip["trip_id"]
            for trip in self.get_trips_for_stop(from_stop_id)
        }

        for first_trip_id in first_trip_ids:

            origin_stop_time = (
                self.get_stop_time_for_trip_at_stop(
                    trip_id=first_trip_id,
                    stop_id=from_stop_id
                )
            )

            if origin_stop_time is None:
                continue

            first_trip_stop_times = (
                self.get_stop_times_for_trip(
                    first_trip_id
                )
            )

            # Stops that are actually ahead of the user on PT1.
            upcoming_stop_ids = {
                stop_time["stop_id"]
                for stop_time in first_trip_stop_times
                if (
                    stop_time["stop_sequence"]
                    > origin_stop_time["stop_sequence"]
                )
            }

            if not upcoming_stop_ids:
                continue

            # Before inventing an inter-stop transfer, find out
            # how early normal PT can already reach the destination.
            best_normal_arrival_minutes = (
                self._find_best_normal_continuation_arrival_minutes(
                    first_trip_id=first_trip_id,
                    from_stop_id=from_stop_id,
                    to_stop_id=to_stop_id
                )
            )

            # --------------------------------------------------------
            # Only now inspect mobility links from upcoming PT1 stops.
            # --------------------------------------------------------

            for transfer_link in self.transfer_links:

                transfer_from_stop_id = (
                    transfer_link["from_stop_id"]
                )

                transfer_to_stop_id = (
                    transfer_link["to_stop_id"]
                )

            # We can only start this transfer from a stop
            # that PT1 actually reaches after the origin.
            if transfer_from_stop_id not in upcoming_stop_ids:
                continue

            transfer_from_stop = self.get_stop_by_id(
                transfer_from_stop_id
            )

            transfer_to_stop = self.get_stop_by_id(
                transfer_to_stop_id
            )

            if (
                transfer_from_stop is None
                or transfer_to_stop is None
            ):
                continue

            # Build the PT1 section:
            # origin -> transfer_from_stop
            first_trip_candidates = self.find_direct_trips(
                from_stop_id=from_stop_id,
                to_stop_id=transfer_from_stop_id
            )

            first_trip = next(
                (
                    trip
                    for trip in first_trip_candidates
                    if trip["trip_id"] == first_trip_id
                ),
                None
            )

            if first_trip is None:
                continue

            # PT2 after the inter-stop movement.
            second_trips = self.find_direct_trips(
                from_stop_id=transfer_to_stop_id,
                to_stop_id=to_stop_id
            )

            for second_trip in second_trips:

                if (
                    first_trip["trip_id"]
                    == second_trip["trip_id"]
                ):
                    continue

                first_arrival = (
                    self.time_service.time_to_minutes(
                        first_trip["arrival_time"]
                    )
                )

                second_departure = (
                    self.time_service.time_to_minutes(
                        second_trip["departure_time"]
                    )
                )

                total_transfer_time_minutes = (
                    second_departure
                    - first_arrival
                )

                if total_transfer_time_minutes <= 0:
                    continue

                walk_transfer_time_minutes = (
                    transfer_link["walk_time_minutes"]
                )

                folding_bike_transfer_time_minutes = (
                    transfer_link[
                        "folding_bike_time_minutes"
                    ]
                    + self.FOLDING_BIKE_TRANSFER_BUFFER_MINUTES
                )

                inter_stop_arrival_minutes = (
                    self.time_service.time_to_minutes(
                        second_trip["arrival_time"]
                    )
                )

                final_arrival_gain_minutes = None

                if best_normal_arrival_minutes is not None:
                    final_arrival_gain_minutes = (
                        best_normal_arrival_minutes
                        - inter_stop_arrival_minutes
                    )

                connections.append({
                    "first_trip": first_trip,

                    "transfer_from_stop":
                        transfer_from_stop,

                    "transfer_to_stop":
                        transfer_to_stop,

                    "second_trip": second_trip,

                    "total_transfer_time_minutes":
                        total_transfer_time_minutes,

                    "walk_transfer_time_minutes":
                        walk_transfer_time_minutes,

                    "folding_bike_transfer_time_minutes":
                        folding_bike_transfer_time_minutes,

                    "walk_transfer_catchable": (
                        walk_transfer_time_minutes
                        <= total_transfer_time_minutes
                    ),

                    "folding_bike_transfer_catchable": (
                        folding_bike_transfer_time_minutes
                        <= total_transfer_time_minutes
                    ),

                    "best_normal_arrival_time": (
                        None
                        if best_normal_arrival_minutes is None
                        else self.time_service.minutes_to_time(
                            best_normal_arrival_minutes
                        )
                    ),

                    "final_arrival_gain_minutes":
                        final_arrival_gain_minutes
                })


        return connections

    def get_transfer_link(
        self,
        from_stop_id: int,
        to_stop_id: int
    ) -> dict | None:

        for link in self.transfer_links:
                
            if (
                link["from_stop_id"] == from_stop_id
                and link["to_stop_id"] == to_stop_id
            ):
                return link

        return None

            
    def evaluate_one_transfer_connection_access(
        self,
        from_stop_id: int,
        to_stop_id: int,
        ready_time: str,
        travel_time_minutes: float,
        safety_buffer_minutes: float = 0
    ) -> list[dict]:

        connections = self.find_one_transfer_connections(
            from_stop_id=from_stop_id,
            to_stop_id=to_stop_id
        )

        return self._evaluate_transfer_connections_access(
            connections=connections,
            ready_time=ready_time,
            travel_time_minutes=travel_time_minutes,
            safety_buffer_minutes=safety_buffer_minutes
        )


    def evaluate_inter_stop_transfer_access(
        self,
        from_stop_id: int,
        to_stop_id: int,
        ready_time: str,
        travel_time_minutes: float,
        safety_buffer_minutes: float = 0
    ) -> list[dict]:

        connections = self.find_inter_stop_transfer_connections(
            from_stop_id=from_stop_id,
            to_stop_id=to_stop_id
        )

        return self._evaluate_transfer_connections_access(
            connections=connections,
            ready_time=ready_time,
            travel_time_minutes=travel_time_minutes,
            safety_buffer_minutes=safety_buffer_minutes
        )

    def _evaluate_transfer_connections_access(
        self,
        connections: list[dict],
        ready_time: str,
        travel_time_minutes: float,
        safety_buffer_minutes: float = 0
    ) -> list[dict]:
        """
        Evaluate whether the user can reach PT1 in time.

        This logic is shared by same-stop and inter-stop transfer
        connections because the type of later transfer does not affect
        whether the first PT departure is catchable.
        """

        evaluated_connections = []

        for connection in connections:

            first_trip = connection["first_trip"]

            catchable = self.can_catch_departure(
                ready_time=ready_time,
                travel_time_minutes=travel_time_minutes,
                departure_time=first_trip["departure_time"],
                safety_buffer_minutes=safety_buffer_minutes
            )

            leave_by_time = (
                self.time_service.calculate_leave_by_time(
                    departure_time=first_trip["departure_time"],
                    travel_time_minutes=travel_time_minutes,
                    safety_buffer_minutes=safety_buffer_minutes
                )
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

            evaluated_connections.append({
                **connection,
                "catchable": catchable,
                "leave_by_time": leave_by_time,
                "wait_before_start_minutes":
                    wait_before_start_minutes
            })

        return evaluated_connections

    def find_unlocked_one_transfer_connections(
        self,
        from_stop_id: int,
        to_stop_id: int,
        ready_time: str,
        baseline_travel_time_minutes: float,
        alternative_travel_time_minutes: float,
        baseline_safety_buffer_minutes: float = 0,
        alternative_safety_buffer_minutes: float = 0
    ) -> list[dict]:

        # Helper Function 
        def connection_key(connection: dict) -> tuple:
                    return (
                        connection["first_trip"]["trip_id"],
                        connection["transfer_stop"]["stop_id"],
                        connection["second_trip"]["trip_id"]
                    )

        # Evaluate the same transfer connections using walking/baseline access.
        baseline_connections = self.evaluate_one_transfer_connection_access(
            from_stop_id=from_stop_id,
            to_stop_id=to_stop_id,
            ready_time=ready_time,
            travel_time_minutes=baseline_travel_time_minutes,
            safety_buffer_minutes=baseline_safety_buffer_minutes
        )

        # Evaluate them again using the faster alternative access mode.

        alternative_connections = self.evaluate_one_transfer_connection_access(
            from_stop_id=from_stop_id,
            to_stop_id=to_stop_id,
            ready_time=ready_time,
            travel_time_minutes=alternative_travel_time_minutes,
            safety_buffer_minutes=alternative_safety_buffer_minutes
        )

        baseline_by_connection = {
            connection_key(connection): connection
            for connection in baseline_connections
        }

        unlocked_connections = []

        for alternative_connection in alternative_connections:

            key = connection_key(alternative_connection)

            baseline_connection = baseline_by_connection[key]

            if (
                not baseline_connection["catchable"]
                and alternative_connection["catchable"]
            ):
                unlocked_connections.append({
                    **alternative_connection,
                    "unlocks_connection": True,
                    "baseline_access": {
                        "catchable": baseline_connection["catchable"],
                        "leave_by_time":
                            baseline_connection["leave_by_time"],
                        "wait_before_start_minutes":
                            baseline_connection[
                                "wait_before_start_minutes"
                            ]
                    }
                })

        return unlocked_connections
        