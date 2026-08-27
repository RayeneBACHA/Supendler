# ============================================================
# STOPS
# ============================================================

stops = [
    {
        "stop_id": 1,
        "stop_name": "Darmstadt Hbf",
        "city": "Darmstadt"
    },
    {
        "stop_id": 2,
        "stop_name": "Luisenplatz",
        "city": "Darmstadt"
    },
    {
        "stop_id": 3,
        "stop_name": "TU Lichtwiese",
        "city": "Darmstadt"
    },
    {
        "stop_id": 4,
        "stop_name": "Schloss",
        "city": "Darmstadt"
    },
    {
        "stop_id": 5,
        "stop_name": "Darmstadt Nord",
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
    }
]

trips = [
    {
        "trip_id": 1,
        "route_id": 1,
        "service_id": "weekday",
        "trip_headsign": "TU Lichtwiese"
    },

    {
        "trip_id": 2,
        "route_id": 1,
        "service_id": "weekday",
        "trip_headsign": "Darmstadt Hbf"
    },

    {
        "trip_id": 3,
        "route_id": 2,
        "service_id": "weekday",
        "trip_headsign": "Darmstadt Nord"
    },

    {
        "trip_id": 4,
        "route_id": 1,
        "service_id": "weekday",
        "trip_headsign": "TU Lichtwiese"
    },

    {
    "trip_id": 5,
    "route_id": 2,
    "service_id": "weekday",
    "trip_headsign": "Darmstadt Nord"
    }
]

stop_times = [
    # ============================================================
    # Trip 1 - Tram 2 - Darmstadt Hbf -> TU Lichtwiese
    # ============================================================

    {
        "trip_id": 1,
        "stop_id": 1,
        "stop_sequence": 1,
        "arrival_time": "12:18",
        "departure_time": "12:18"
    },
    {
        "trip_id": 1,
        "stop_id": 2,
        "stop_sequence": 2,
        "arrival_time": "12:25",
        "departure_time": "12:25"
    },
    {
        "trip_id": 1,
        "stop_id": 4,
        "stop_sequence": 3,
        "arrival_time": "12:28",
        "departure_time": "12:28"
    },
    {
        "trip_id": 1,
        "stop_id": 3,
        "stop_sequence": 4,
        "arrival_time": "12:37",
        "departure_time": "12:37"
    },

    # ============================================================
    # Trip 2 - Tram 2 - TU Lichtwiese -> Darmstadt Hbf
    # ============================================================

    {
        "trip_id": 2,
        "stop_id": 3,
        "stop_sequence": 1,
        "arrival_time": "12:25",
        "departure_time": "12:25"
    },
    {
        "trip_id": 2,
        "stop_id": 4,
        "stop_sequence": 2,
        "arrival_time": "12:34",
        "departure_time": "12:34"
    },
    {
        "trip_id": 2,
        "stop_id": 2,
        "stop_sequence": 3,
        "arrival_time": "12:37",
        "departure_time": "12:37"
    },
    {
        "trip_id": 2,
        "stop_id": 1,
        "stop_sequence": 4,
        "arrival_time": "12:45",
        "departure_time": "12:45"
    },

    # ============================================================
    # Trip 3 - RB - Darmstadt Hbf -> Darmstadt Nord
    # ============================================================

    {
        "trip_id": 3,
        "stop_id": 1,
        "stop_sequence": 1,
        "arrival_time": "12:30",
        "departure_time": "12:30"
    },
    {
        "trip_id": 3,
        "stop_id": 5,
        "stop_sequence": 2,
        "arrival_time": "12:35",
        "departure_time": "12:35"
    },

    # ============================================================
    # Trip 4 - Tram 2 - Darmstadt Hbf -> TU Lichtwiese
    # ============================================================

    {
        "trip_id": 4,
        "stop_id": 1,
        "stop_sequence": 1,
        "arrival_time": "12:38",
        "departure_time": "12:38"
    },
    {
        "trip_id": 4,
        "stop_id": 2,
        "stop_sequence": 2,
        "arrival_time": "12:45",
        "departure_time": "12:45"
    },
    {
        "trip_id": 4,
        "stop_id": 4,
        "stop_sequence": 3,
        "arrival_time": "12:48",
        "departure_time": "12:48"
    },
    {
        "trip_id": 4,
        "stop_id": 3,
        "stop_sequence": 4,
        "arrival_time": "12:57",
        "departure_time": "12:57"
    },

    # ============================================================
    # Trip 3 - RB - Darmstadt Hbf -> Darmstadt Nord
    # ============================================================

    {
    "trip_id": 5,
    "stop_id": 1,
    "arrival_time": "12:50",
    "departure_time": "12:50",
    "stop_sequence": 1
    },
    {
    "trip_id": 5,
    "stop_id": 5,
    "arrival_time": "12:55",
    "departure_time": "12:55",
    "stop_sequence": 2
    }

]