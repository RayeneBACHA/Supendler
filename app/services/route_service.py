from app.schemas.route import RouteOptionsRequest, SegmentRole
from app.services.mobility_option_service import MobilityOptionService
from app.services.public_transport_service import PublicTransportService
from app.schemas.route_response import RouteProfile

class RouteService:
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
        If the user has a folding bike, folding-bike access is evaluated 
        against walking to detect departures that the bike unlocks.
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

        if walking_access is None or walking_egress is None:
            return routes

        #------------------------------------------------------------
        # 1. Walking baseline
        #------------------------------------------------------------

        walking_trips = self.public_transport_service.evaluate_direct_trip_access(
            from_station_id=request.station_pair.start_station_id,
            to_station_id=request.station_pair.end_station_id,
            ready_time=request.journey.ready_time,
            travel_time_minutes=walking_access["time_minutes"]
        )

        for trip in walking_trips:

            if not trip["catchable"]:
                continue

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

        if not request.user.has_folding_bike:
            return routes

        folding_bike_access = self._find_folding_bike_option(
            access_options
        )

        folding_bike_egress = self._find_folding_bike_option(
            egress_options
        )

        if folding_bike_access is None or folding_bike_egress is None:
            return routes

        bike_trips = self.public_transport_service.evaluate_direct_trip_access(
            from_station_id=request.station_pair.start_station_id,
            to_station_id=request.station_pair.end_station_id,
            ready_time=request.journey.ready_time,
            travel_time_minutes=folding_bike_access["time_minutes"]
        )

        unlocked_trips = (
            self.public_transport_service.find_unlocked_direct_trips(
                from_station_id=request.station_pair.start_station_id,
                to_station_id=request.station_pair.end_station_id,
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