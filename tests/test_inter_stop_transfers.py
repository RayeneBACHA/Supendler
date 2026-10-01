from app.services.public_transport_service import PublicTransportService
from app.services.time_service import TimeService


def build_service(
    normal_trip_departure: str = "13:20",
    normal_trip_arrival: str = "13:25"
) -> PublicTransportService:
    """
    Build a tiny isolated timetable for inter-stop transfer tests.

    Scenario:

    TU Lichtwiese
        ↓ Trip 2
    Darmstadt Hbf
        ↓ walk / folding bike
    Rhein/Neckarstraße
        ↓ Trip 6
    Darmstadt Nord

    A normal same-stop continuation also exists:

    TU Lichtwiese
        ↓ Trip 2
    Darmstadt Hbf
        ↓ Trip 5
    Darmstadt Nord
    """

    stops = [
        {
            "stop_id": 1,
            "stop_name": "Darmstadt Hbf",
            "city": "Darmstadt"
        },
        {
            "stop_id": 3,
            "stop_name": "TU Lichtwiese",
            "city": "Darmstadt"
        },
        {
            "stop_id": 5,
            "stop_name": "Darmstadt Nord",
            "city": "Darmstadt"
        },
        {
            "stop_id": 6,
            "stop_name": "Rhein/Neckarstraße",
            "city": "Darmstadt"
        }
    ]

    routes = [
        {
            "route_id": 1,
            "route_short_name": "2",
            "route_type": "tram"
        },
        {
            "route_id": 2,
            "route_short_name": "RB",
            "route_type": "train"
        },
        {
            "route_id": 3,
            "route_short_name": "X",
            "route_type": "bus"
        }
    ]

    trips = [
        {
            "trip_id": 2,
            "route_id": 1,
            "service_id": "weekday",
            "trip_headsign": "Darmstadt Hbf"
        },
        {
            "trip_id": 5,
            "route_id": 2,
            "service_id": "weekday",
            "trip_headsign": "Darmstadt Nord"
        },
        {
            "trip_id": 6,
            "route_id": 3,
            "service_id": "weekday",
            "trip_headsign": "Darmstadt Nord"
        }
    ]

    stop_times = [
        # --------------------------------------------------------
        # Trip 2: TU Lichtwiese -> Darmstadt Hbf
        # --------------------------------------------------------

        {
            "trip_id": 2,
            "stop_id": 3,
            "stop_sequence": 1,
            "arrival_time": "12:25",
            "departure_time": "12:25"
        },
        {
            "trip_id": 2,
            "stop_id": 1,
            "stop_sequence": 2,
            "arrival_time": "12:45",
            "departure_time": "12:45"
        },

        # --------------------------------------------------------
        # Trip 5: normal same-stop continuation
        # --------------------------------------------------------

        {
            "trip_id": 5,
            "stop_id": 1,
            "stop_sequence": 1,
            "arrival_time": normal_trip_departure,
            "departure_time": normal_trip_departure
        },
        {
            "trip_id": 5,
            "stop_id": 5,
            "stop_sequence": 2,
            "arrival_time": normal_trip_arrival,
            "departure_time": normal_trip_arrival
        },

        # --------------------------------------------------------
        # Trip 6: inter-stop connection
        # --------------------------------------------------------

        {
            "trip_id": 6,
            "stop_id": 6,
            "stop_sequence": 1,
            "arrival_time": "12:51",
            "departure_time": "12:51"
        },
        {
            "trip_id": 6,
            "stop_id": 5,
            "stop_sequence": 2,
            "arrival_time": "13:01",
            "departure_time": "13:01"
        }
    ]

    transfer_links = [
        {
            "from_stop_id": 1,
            "to_stop_id": 6,
            "walk_time_minutes": 8,
            "folding_bike_time_minutes": 3
        }
    ]

    return PublicTransportService(
        stops=stops,
        routes=routes,
        trips=trips,
        stop_times=stop_times,
        transfer_links=transfer_links,
        time_service=TimeService()
    )


def test_folding_bike_can_unlock_inter_stop_transfer():
    """
    Trip 2 arrives Hbf at 12:45.
    Trip 6 leaves Rhein/Neckarstraße at 12:51.

    Transfer window = 6 minutes.

    Walking needs 8 minutes -> misses.
    Folding bike needs 3 + 1 buffer = 4 minutes -> catches.
    """

    service = build_service()

    connections = service.find_inter_stop_transfer_connections(
        from_stop_id=3,
        to_stop_id=5
    )

    assert len(connections) == 1

    connection = connections[0]

    assert connection["first_trip"]["trip_id"] == 2
    assert connection["second_trip"]["trip_id"] == 6

    assert connection["transfer_from_stop"]["stop_id"] == 1
    assert connection["transfer_to_stop"]["stop_id"] == 6

    assert connection["total_transfer_time_minutes"] == 6

    assert connection["walk_transfer_time_minutes"] == 8
    assert connection["walk_transfer_catchable"] is False

    assert connection["folding_bike_transfer_time_minutes"] == 4
    assert connection["folding_bike_transfer_catchable"] is True


def test_inter_stop_transfer_has_24_minute_arrival_gain():
    """
    Normal PT arrives at 13:25.

    The folding-bike inter-stop connection reaches the final PT stop
    at 13:01.

    Gain = 24 minutes.
    """

    service = build_service(
        normal_trip_departure="13:20",
        normal_trip_arrival="13:25"
    )

    connections = service.find_inter_stop_transfer_connections(
        from_stop_id=3,
        to_stop_id=5
    )

    connection = connections[0]

    assert connection["best_normal_arrival_time"] == "13:25"
    assert connection["final_arrival_gain_minutes"] == 24


def test_inter_stop_transfer_can_exist_with_only_9_minute_gain():
    """
    PublicTransportService should still discover the connection even
    when its final-arrival gain is below the product threshold.

    Normal PT arrives 13:10.
    Inter-stop PT arrives 13:01.

    Gain = 9 minutes.

    RouteService is responsible for rejecting it later.
    """

    service = build_service(
        normal_trip_departure="13:05",
        normal_trip_arrival="13:10"
    )

    connections = service.find_inter_stop_transfer_connections(
        from_stop_id=3,
        to_stop_id=5
    )

    assert len(connections) == 1

    connection = connections[0]

    assert connection["final_arrival_gain_minutes"] == 9


def test_walking_does_not_unlock_inter_stop_transfer():
    """
    The transfer is not a walking-unlocked connection because walking
    requires 8 minutes while only 6 minutes are available.
    """

    service = build_service()

    connections = service.find_inter_stop_transfer_connections(
        from_stop_id=3,
        to_stop_id=5
    )

    connection = connections[0]

    assert connection["walk_transfer_catchable"] is False