from app.schemas.route import RouteOptionsRequest, SegmentRole
from app.services.mobility_option_service import MobilityOptionService
from app.services.public_transport_service import PublicTransportService


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

        public_transport_trips = (
            self.public_transport_service.find_direct_trips(
                request.station_pair.start_station_id,
                request.station_pair.end_station_id
            )
        )

        if public_transport_trips:
            route_options.extend(
                self._build_public_transport_routes(
                    request=request,
                    trips=public_transport_trips
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

            mobility_leg = self._create_mobility_leg(option)

            routes.append({
                "route_type": "direct",

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
        trips: list[dict]
    ) -> list[dict]:

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

        for trip in trips:

            # Normal combinations:
            # walk/shared bike/shared scooter
            routes.extend(
                self._combine_normal_options(
                    access_options=access_options,
                    egress_options=egress_options,
                    trip=trip
                )
            )

            # Folding bike combination
            folding_bike_route = (
                self._build_folding_bike_route(
                    access_options=access_options,
                    egress_options=egress_options,
                    trip=trip
                )
            )

            if folding_bike_route is not None:
                routes.append(folding_bike_route)

        return routes


    def _combine_normal_options(
        self,
        access_options: list[dict],
        egress_options: list[dict],
        trip: dict
    ) -> list[dict]:

        routes = []

        normal_access_options = [
            option
            for option in access_options
            if option["source"] != "folding_bike"
        ]

        normal_egress_options = [
            option
            for option in egress_options
            if option["source"] != "folding_bike"
        ]

        for access_option in normal_access_options:

            for egress_option in normal_egress_options:

                route = self._create_public_transport_route(
                    access_option=access_option,
                    trip=trip,
                    egress_option=egress_option
                )

                routes.append(route)

        return routes


    def _build_folding_bike_route(
        self,
        access_options: list[dict],
        egress_options: list[dict],
        trip: dict
    ) -> dict | None:

        folding_bike_access = (
            self._find_folding_bike_option(access_options)
        )

        folding_bike_egress = (
            self._find_folding_bike_option(egress_options)
        )

        if (
            folding_bike_access is None
            or folding_bike_egress is None
        ):
            return None

        return self._create_public_transport_route(
            access_option=folding_bike_access,
            trip=trip,
            egress_option=folding_bike_egress
        )


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
        egress_option: dict
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

            "duration_minutes": trip["duration_minutes"],

            "stops": trip["stops"]
        }

        egress_leg = self._create_mobility_leg(
            egress_option
        )

        return {
            "route_type": "public_transport_combo",

            "total_time_minutes": round(
                total_time,
                1
            ),

            "modes": [
                access_option["mode"],
                trip["line_type"],
                egress_option["mode"]
            ],

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