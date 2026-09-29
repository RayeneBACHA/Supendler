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
    },
    {
        "stop_id": 6,
        "stop_name": "Rhein/Neckarstraße",
        "city": "Darmstadt"
    }
]


# ============================================================
# ROUTES
# ============================================================

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


# ============================================================
# TRIPS
# ============================================================

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
    },
    {
        "trip_id": 6,
        "route_id": 3,
        "service_id": "weekday",
        "trip_headsign": "Darmstadt Nord"
    }
]


# ============================================================
# STOP TIMES
# ============================================================

stop_times = [

    # ========================================================
    # Trip 1 - Tram 2 - Darmstadt Hbf -> TU Lichtwiese
    # ========================================================

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

    # ========================================================
    # Trip 2 - Tram 2 - TU Lichtwiese -> Darmstadt Hbf
    # ========================================================

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

    # ========================================================
    # Trip 3 - RB - Darmstadt Hbf -> Darmstadt Nord
    # Earlier train that leaves before Trip 2 reaches Hbf
    # ========================================================

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

    # ========================================================
    # Trip 4 - Tram 2 - Darmstadt Hbf -> TU Lichtwiese
    # ========================================================

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

    # ========================================================
    # Trip 5 - RB - Darmstadt Hbf -> Darmstadt Nord
    #
    # This is intentionally late.
    # It represents the best normal PT continuation after
    # arriving at Hbf with Trip 2.
    #
    # Normal final arrival:
    # 13:25
    # ========================================================

    {
        "trip_id": 5,
        "stop_id": 1,
        "stop_sequence": 1,
        "arrival_time": "13:20",
        "departure_time": "13:20"
    },
    {
        "trip_id": 5,
        "stop_id": 5,
        "stop_sequence": 2,
        "arrival_time": "13:25",
        "departure_time": "13:25"
    },

    # ========================================================
    # Trip 6 - Bus X - Rhein/Neckarstraße -> Darmstadt Nord
    #
    # This is the PT2 connection that the folding bike
    # should unlock.
    #
    # Trip 2 reaches Hbf at 12:45.
    # Bus X leaves Rhein/Neckarstraße at 12:51.
    #
    # Available transfer time = 6 min
    # walking = 8 min -> misses
    # folding bike = 3 min + 1 min buffer = 4 min -> catches
    #
    # Final arrival:
    # 13:01
    #
    # Compared with normal PT arrival at 13:25:
    # gain = 24 min
    # ========================================================

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


# ============================================================
# TRANSFER LINKS
# ============================================================

transfer_links = [
    {
        "from_stop_id": 1,   # Darmstadt Hbf
        "to_stop_id": 6,     # Rhein/Neckarstraße

        "walk_time_minutes": 8,
        "folding_bike_time_minutes": 3
    }
]