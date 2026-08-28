from app.schemas.route import RouteOptionsRequest, SegmentRole
from app.services.mobility_option_service import MobilityOptionService
from app.services.public_transport_service import PublicTransportService
from app.schemas.route_response import RouteProfile

class RouteService:

    MIN_SHARED_FINAL_ARRIVAL_GAIN_MINUTES = 10

    def __init__(
        self,
        mobility_option_service: MobilityOptionService,
        public_transport_service: PublicTransportService
    ):
        self.mobility_option_service = mobility_option_service
        self.public_transport_service = public_transport_service


    def generate_route_options(
        self,
        request: RouteOptionsRequest
    ) -> dict:

        route_options = []

        # -----------------------------------
        # 1. Direct routes
        # -----------------------------------

        direct_options = self.mobility_option_service.generate_options(
            segment=request.direct,
            segment_role=SegmentRole.direct,
            has_folding_bike=request.user.has_folding_bike
        )

        route_options.extend(
            self._build_direct_routes(direct_options)
        )

        # -----------------------------------
        # 2. Public transport routes
        # -----------------------------------

        route_options.extend(
            self._build_public_transport_routes(
                request=request
            )
        )
        # -----------------------------------
        # 3. Sort routes
        # -----------------------------------

        sorted_options = sorted(
            route_options,
            key=lambda route: route["total_time_minutes"]
        )

        return {
            "option_count": len(sorted_options),
            "fastest_option": sorted_options[0],
            "options": sorted_options
        }


    def _build_direct_routes(
        self,
        direct_options: list[dict]
    ) -> list[dict]:

        routes = []

        for option in direct_options:

            profile = self._get_direct_route_profile(option)

            mobility_leg = self._create_mobility_leg(option)

            routes.append({
                "route_type": "direct",
                "profile": profile,

                "total_time_minutes": option["time_minutes"],

                "modes": [
                    option["mode"]
                ],

                "legs": [
                    mobility_leg
                ]
            })

        return routes


    def _build_public_transport_routes(
        self,
        request: RouteOptionsRequest,
    ) -> list[dict]:

        """
        Build timetable-aware public transport routes.

        Walking is the baseline mobility profile.

        Alternative access modes can unlock public transport departures
        that walking cannot reach in time.

        Shared egress is included when it improves final arrival time
        by the configured minimum threshold.
        """

        routes = []

        access_options = (
            self.mobility_option_service.generate_options(
                segment=request.access,
                segment_role=SegmentRole.access,
                has_folding_bike=request.user.has_folding_bike
            )
        )

        egress_options = (
            self.mobility_option_service.generate_options(
                segment=request.egress,
                segment_role=SegmentRole.egress,
                has_folding_bike=request.user.has_folding_bike
            )
        )

        walking_access = self._find_walking_option(
            access_options
        )

        walking_egress = self._find_walking_option(
            egress_options
        )


        #------------------------------------------------------------
        # 1. Walking baseline
        #------------------------------------------------------------

        walking_trips = self.public_transport_service.evaluate_direct_trip_access(
            from_stop_id=request.stop_pair.start_stop_id,
            to_stop_id=request.stop_pair.end_stop_id,
            ready_time=request.journey.ready_time,
            travel_time_minutes=walking_access["time_minutes"]
        )

        catchable_walking_trips = [
            trip
            for trip in walking_trips
            if trip["catchable"]
        ]

        for trip in catchable_walking_trips:


            routes.append(
                self._create_public_transport_route(
                        access_option=walking_access,
                        trip=trip,
                        egress_option=walking_egress,
                        profile=RouteProfile.pt_walk,
                        leave_by_time=trip["leave_by_time"],
                        wait_before_start_minutes=trip["wait_before_start_minutes"]
                )
            )

        #------------------------------------------------------------
        # 2. Folding-bike profile
        #------------------------------------------------------------

        if request.user.has_folding_bike:

            folding_bike_access = self._find_folding_bike_option(
                access_options
            )

            folding_bike_egress = self._find_folding_bike_option(
                egress_options
            )

            bike_trips = self.public_transport_service.evaluate_direct_trip_access(
                from_stop_id=request.stop_pair.start_stop_id,
                to_stop_id=request.stop_pair.end_stop_id,
                ready_time=request.journey.ready_time,
                travel_time_minutes=folding_bike_access["time_minutes"]
            )

            unlocked_trips = (
                self.public_transport_service.find_unlocked_direct_trips(
                    from_stop_id=request.stop_pair.start_stop_id,
                    to_stop_id=request.stop_pair.end_stop_id,
                    ready_time=request.journey.ready_time,
                    baseline_travel_time_minutes=walking_access["time_minutes"],
                    alternative_travel_time_minutes=folding_bike_access["time_minutes"]
                )
            )

            unlocked_trips_ids = {
                trip["trip_id"]
                for trip in unlocked_trips
            }

            for trip in bike_trips:

                if not trip["catchable"]:
                    continue

                benefit = None

                if trip["trip_id"] in unlocked_trips_ids:
                    benefit = "unlocks_connection"

                routes.append(
                    self._create_public_transport_route(
                        access_option=folding_bike_access,
                        trip=trip,
                        egress_option=folding_bike_egress,
                        profile=RouteProfile.pt_folding_bike,
                        leave_by_time=trip["leave_by_time"],
                        wait_before_start_minutes=trip[
                            "wait_before_start_minutes"
                        ],
                        benefit=benefit
                    )
                )

        shared_access_options = self._find_shared_options(
            access_options
        )

        shared_egress_options = self._find_shared_options(
            egress_options
        )

        # ------------------------------------------------------------
        # 3. Shared-mobility access profile
        # ------------------------------------------------------------

        for shared_access in shared_access_options:

            unlocked_trips = (
                self.public_transport_service.find_unlocked_direct_trips(
                    from_stop_id=request.stop_pair.start_stop_id,
                    to_stop_id=request.stop_pair.end_stop_id,
                    ready_time=request.journey.ready_time,
                    baseline_travel_time_minutes=walking_access["time_minutes"],
                    alternative_travel_time_minutes=shared_access["time_minutes"]
                )
            )

            for trip in unlocked_trips:

                routes.append(
                    self._create_public_transport_route(
                        access_option=shared_access,
                        trip=trip,
                        egress_option=walking_egress,
                        profile=RouteProfile.pt_shared,
                        leave_by_time=trip["leave_by_time"],
                        wait_before_start_minutes=trip[
                            "wait_before_start_minutes"
                        ],
                        benefit="unlocks_connection"
                    )
                )

        # ------------------------------------------------------------
        # 4. Shared-mobility egress profile
        # ------------------------------------------------------------
        
        for shared_egress in shared_egress_options:

            final_arrival_gain_minutes = (
                walking_egress["time_minutes"]
                - shared_egress["time_minutes"]
            )

            if final_arrival_gain_minutes < self.MIN_SHARED_FINAL_ARRIVAL_GAIN_MINUTES:
                continue

            for trip in catchable_walking_trips:

                routes.append(
                    self._create_public_transport_route(
                        access_option=walking_access,
                        trip=trip,
                        egress_option=shared_egress,
                        profile=RouteProfile.pt_shared,
                        leave_by_time=trip["leave_by_time"],
                        wait_before_start_minutes= trip[
                            "wait_before_start_minutes"
                        ],
                        benefit="faster_arrival"
                    )
                )

        # ------------------------------------------------------------
        # 5. One-transfer walking baseline
        # ------------------------------------------------------------

        walking_transfer_connections = (
            self.public_transport_service
            .evaluate_one_transfer_connection_access(
                from_stop_id=request.stop_pair.start_stop_id,
                to_stop_id=request.stop_pair.end_stop_id,
                ready_time=request.journey.ready_time,
                travel_time_minutes=walking_access["time_minutes"]
            )
        )

        catchable_walking_transfer_connections = [
            connection 
            for connection in walking_transfer_connections
            if connection["catchable"]
        ]

        for connection in catchable_walking_transfer_connections:

            routes.append(
                self._create_public_transport_transfer_route(
                    access_option=walking_access,
                    connection=connection,
                    egress_option=walking_egress,
                    profile=RouteProfile.pt_walk,
                    leave_by_time=connection["leave_by_time"],
                    wait_before_start_minutes=connection[
                        "wait_before_start_minutes"
                    ]
                )
            )


        # ------------------------------------------------------------
        # 6. folding_bike one-transfer PT
        # ------------------------------------------------------------

        if request.user.has_folding_bike:

            folding_transfer_connections = (
                self.public_transport_service
                .evaluate_one_transfer_connection_access(
                    from_stop_id=request.stop_pair.start_stop_id,
                    to_stop_id=request.stop_pair.end_stop_id,
                    ready_time=request.journey.ready_time,
                    travel_time_minutes=
                        folding_bike_access["time_minutes"]
                )
            )

            unlocked_folding_bike_connections = (
                self.public_transport_service
                .find_unlocked_one_transfer_connections(
                    from_stop_id=request.stop_pair.start_stop_id,
                    to_stop_id=request.stop_pair.end_stop_id,
                    ready_time=request.journey.ready_time,
                    baseline_travel_time_minutes=
                        walking_access["time_minutes"],
                    alternative_travel_time_minutes=
                        folding_bike_access["time_minutes"]
                )
            )

            unlocked_connection_keys = {
                (
                    connection["first_trip"]["trip_id"],
                    connection["transfer_stop"]["stop_id"],
                    connection["second_trip"]["trip_id"]
                )
                for connection in unlocked_folding_bike_connections
            }

            for connection in folding_transfer_connections:

                if not connection["catchable"]:
                    continue

                connection_key = (
                    connection["first_trip"]["trip_id"],
                    connection["transfer_stop"]["stop_id"],
                    connection["second_trip"]["trip_id"]
                )

                benefit = None

                if connection_key in unlocked_connection_keys:
                    benefit = "unlocks_connection"

                routes.append(
                    self._create_public_transport_transfer_route(
                        access_option=folding_bike_access,
                        connection=connection,
                        egress_option=folding_bike_egress,
                        profile=RouteProfile.pt_folding_bike,
                        leave_by_time=connection["leave_by_time"],
                        wait_before_start_minutes=connection[
                            "wait_before_start_minutes"
                        ],
                        benefit=benefit
                    )
                )

        return routes


    def _find_folding_bike_option(
        self,
        options: list[dict]
    ) -> dict | None:

        for option in options:

            if option["source"] == "folding_bike":
                return option

        return None


    def _create_public_transport_route(
        self,
        access_option: dict,
        trip: dict,
        egress_option: dict,
        profile: RouteProfile,
        leave_by_time: str | None = None,
        wait_before_start_minutes: float | None = None,
        benefit: str | None = None
    ) -> dict:

        total_time = (
            access_option["time_minutes"]
            + trip["duration_minutes"]
            + egress_option["time_minutes"]
        )

        access_leg = self._create_mobility_leg(
            access_option
        )

        public_transport_leg = {
            "leg_type": "public_transport",

            "trip_id": trip["trip_id"],

            "line": trip["line"],
            "line_type": trip["line_type"],
            "destination": trip["destination"],

            "departure_time": trip["departure_time"],
            "arrival_time": trip["arrival_time"],

            "duration_minutes": trip["duration_minutes"],
            "stops": trip["stops"]
        }

        egress_leg = self._create_mobility_leg(
            egress_option
        )

        return {
            "route_type": "public_transport_combo",
            "profile": profile,

            "total_time_minutes": round(
                total_time,
                1
            ),

            "modes": [
                access_option["mode"],
                trip["line_type"],
                egress_option["mode"]
            ],

            "leave_by_time": leave_by_time,
            "wait_before_start_minutes": wait_before_start_minutes,
            "benefit": benefit,

            "legs": [
                access_leg,
                public_transport_leg,
                egress_leg
            ]
        }


    def _create_mobility_leg(
        self,
        option: dict
    ) -> dict:

        return {
            "leg_type": "mobility",

            "role": option["segment_role"],

            "mode": option["mode"],
            "source": option["source"],

            "time_minutes": option["time_minutes"],

            "actions": option["steps"]
        }

    def _find_walking_option(
            self,
            options: list[dict]
    ) -> dict | None:
        """
        Find the always-available walking option for a mobility segment.
        """

        for option in options:
            if option["mode"] == "walk":
                return option

        return None


    def _get_direct_route_profile(
            self,
            option: dict
    ) -> RouteProfile:
        """
        Group a direct mobility option into the frontend route families.
        """

        if option["mode"] == "walk":
            return RouteProfile.direct_walk

        if option["source"] == "folding_bike":
            return RouteProfile.direct_bike

        return RouteProfile.direct_shared

    def _find_shared_options(
        self,
        options: list[dict]
    ) -> list[dict]:

        return [
            option
            for option in options
            if option["source"] in {
                "shared_bike",
                "shared_scooter"
            }
        ]


    def _create_transfer_leg(
        self,
        connection: dict,
    ) -> dict:

        transfer_stop = connection["transfer_stop"]

        return {
            "leg_type": "transfer",
            "stop_id": transfer_stop["stop_id"],
            "stop_name": transfer_stop["stop_name"],
            "total_time_minutes":
                connection["total_transfer_time_minutes"],
            "walk_time_minutes":
                connection["walk_transfer_time_minutes"]
        }


    def _create_public_transport_transfer_route(
        self,
        access_option: dict,
        connection: dict,
        egress_option: dict,
        profile: RouteProfile,
        leave_by_time: str | None = None,
        wait_before_start_minutes: float | None = None,
        benefit: str | None = None
    ) -> dict:
        first_trip = connection["first_trip"]
        second_trip = connection["second_trip"]

        access_leg = self._create_mobility_leg(
            access_option
        )

        first_pt_leg = {
            "leg_type": "public_transport",
            "trip_id": first_trip["trip_id"],
            "line": first_trip["line"],
            "line_type": first_trip["line_type"],
            "destination": first_trip["destination"],
            "departure_time": first_trip["departure_time"],
            "arrival_time": first_trip["arrival_time"],
            "duration_minutes": first_trip["duration_minutes"],
            "stops": first_trip["stops"]
        }

        transfer_leg = self._create_transfer_leg(
            connection
        )

        second_pt_leg = {
            "leg_type": "public_transport",
            "trip_id": second_trip["trip_id"],
            "line": second_trip["line"],
            "line_type": second_trip["line_type"],
            "destination": second_trip["destination"],
            "departure_time": second_trip["departure_time"],
            "arrival_time": second_trip["arrival_time"],
            "duration_minutes": second_trip["duration_minutes"],
            "stops": second_trip["stops"]
        }

        egress_leg = self._create_mobility_leg(
            egress_option
        )

        total_time = (
            access_option["time_minutes"]
            + first_trip["duration_minutes"]
            + connection["total_transfer_time_minutes"]
            + second_trip["duration_minutes"]
            + egress_option["time_minutes"]
        )


        return {
            "route_type": "public_transport_combo",
            "profile": profile,
            "total_time_minutes": round(total_time, 1),
            "modes": [
                access_option["mode"],
                first_trip["line_type"],
                second_trip["line_type"],
                egress_option["mode"]
            ],
            "leave_by_time": leave_by_time,
            "wait_before_start_minutes":
                wait_before_start_minutes,
            "benefit": benefit,
            "legs": [
                access_leg,
                first_pt_leg,
                transfer_leg,
                second_pt_leg,
                egress_leg
            ]
        }


        