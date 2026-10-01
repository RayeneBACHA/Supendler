from types import SimpleNamespace

from app.services.route_service import RouteService

# ============================================================
# FAKE MOBILITY SERVICE
# ============================================================

class FakeMobilityOptionService:
    """
    Gives RouteService predictable walking and folding-bike options.

    We are not testing mobility calculations here.
    We only want to test RouteService's decision about whether an
    inter-stop transfer is valuable enough to show.
    """

    def generate_options(
        self,
        segment,
        segment_role,
        has_folding_bike
    ):
        role = (
            segment_role.value
            if hasattr(segment_role, "value")
            else segment_role
        )

        if role == "access":
            return [
                {
                    "segment_role": "access",
                    "mode": "walk",
                    "source": "always_available",
                    "time_minutes": 20,
                    "steps": []
                },
                {
                    "segment_role": "access",
                    "mode": "bike",
                    "source": "folding_bike",
                    "time_minutes": 7,
                    "steps": []
                }
            ]

        if role == "egress":
            return [
                {
                    "segment_role": "egress",
                    "mode": "walk",
                    "source": "always_available",
                    "time_minutes": 6,
                    "steps": []
                },
                {
                    "segment_role": "egress",
                    "mode": "bike",
                    "source": "folding_bike",
                    "time_minutes": 3,
                    "steps": []
                }
            ]

        return []

# ============================================================
# FAKE PUBLIC TRANSPORT SERVICE
# ============================================================
class FakePublicTransportService:
    """
    Fake PT service used to isolate RouteService's inter-stop logic.

    All normal/direct PT searches return no routes.
    Only the inter-stop transfer candidate is returned.
    """

    def __init__(self, final_arrival_gain_minutes):
        self.final_arrival_gain_minutes = (
            final_arrival_gain_minutes
        )

    # --------------------------------------------------------
    # Direct PT
    # --------------------------------------------------------

    def evaluate_direct_trip_access(
        self,
        *args,
        **kwargs
    ):
        return []

    def find_unlocked_direct_trips(
        self,
        *args,
        **kwargs
    ):
        return []

    # --------------------------------------------------------
    # Normal same-stop transfers
    # --------------------------------------------------------

    def evaluate_one_transfer_connection_access(
        self,
        *args,
        **kwargs
    ):
        return []

    def find_unlocked_one_transfer_connections(
        self,
        *args,
        **kwargs
    ):
        return []

    # --------------------------------------------------------
    # Inter-stop transfer
    # --------------------------------------------------------

    def evaluate_inter_stop_transfer_access(
        self,
        *args,
        **kwargs
    ):
        return [
            {
                "first_trip": {
                    "trip_id": 2,
                    "line": "2",
                    "line_type": "tram",
                    "destination": "Darmstadt Hbf",
                    "departure_time": "12:25",
                    "arrival_time": "12:45",
                    "duration_minutes": 20,
                    "stops": []
                },

                "transfer_from_stop": {
                    "stop_id": 1,
                    "stop_name": "Darmstadt Hbf"
                },

                "transfer_to_stop": {
                    "stop_id": 6,
                    "stop_name": "Rhein/Neckarstraße"
                },

                "second_trip": {
                    "trip_id": 6,
                    "line": "X",
                    "line_type": "bus",
                    "destination": "Darmstadt Nord",
                    "departure_time": "12:51",
                    "arrival_time": "13:01",
                    "duration_minutes": 10,
                    "stops": []
                },

                # Six-minute timetable window:
                # 12:45 -> 12:51
                "total_transfer_time_minutes": 6,

                # Walking misses.
                "walk_transfer_time_minutes": 8,
                "walk_transfer_catchable": False,

                # Folding bike catches.
                "folding_bike_transfer_time_minutes": 4,
                "folding_bike_transfer_catchable": True,

                # Folding-bike access can catch PT1.
                "catchable": True,
                "leave_by_time": "12:18",
                "wait_before_start_minutes": 8,

                # Value that RouteService must apply its
                # product threshold to.
                "final_arrival_gain_minutes":
                    self.final_arrival_gain_minutes
            }
        ]

# ============================================================
# TEST HELPERS
# ============================================================

def build_request():
    """
    Build only the request fields used by
    RouteService._build_public_transport_routes().

    SimpleNamespace keeps this unit test focused on RouteService
    instead of Pydantic validation.
    """

    return SimpleNamespace(
        journey=SimpleNamespace(
            ready_time="12:10"
        ),

        stop_pair=SimpleNamespace(
            start_stop_id=3,
            end_stop_id=5
        ),

        user=SimpleNamespace(
            has_folding_bike=True
        ),

        access=SimpleNamespace(),
        egress=SimpleNamespace()
    )

def build_route_service(
    final_arrival_gain_minutes
):
    return RouteService(
        mobility_option_service=FakeMobilityOptionService(),

        public_transport_service=FakePublicTransportService(
            final_arrival_gain_minutes=
                final_arrival_gain_minutes
        )
    )

def find_inter_stop_routes(routes):
    """
    Return only routes containing a real inter_stop transfer leg.
    """

    return [
        route
        for route in routes
        if any(
            leg["leg_type"] == "inter_stop_transfer"
            for leg in route["legs"]
        )
    ]

# ============================================================
# TESTS
# ============================================================

def test_24_minute_gain_inter_stop_route_is_included():
    """
    24 minutes >= 20-minute product threshold.

    The route should be recommended.
    """

    route_service = build_route_service(
        final_arrival_gain_minutes=24
    )

    request = build_request()

    routes = route_service._build_public_transport_routes(
        request
    )

    inter_stop_routes = find_inter_stop_routes(
        routes=routes
    )

    assert len(inter_stop_routes) == 1

    route = inter_stop_routes[0]

    assert route["benefit"] == "unlocks_connection"

    assert route["modes"] == [
        "bike",
        "tram",
        "bike",
        "bus",
        "bike"
    ]

def test_9_minute_gain_inter_stop_route_is_rejected():
    """
    9 minutes < 20-minute product threshold.

    The connection is physically possible, but it is not valuable
    enough to recommend to the user.
    """

    route_service = build_route_service(
        final_arrival_gain_minutes=9
    )

    request = build_request()

    routes = route_service._build_public_transport_routes(
        request
    )

    inter_stop_routes = find_inter_stop_routes(
        routes
    )

    assert inter_stop_routes == []