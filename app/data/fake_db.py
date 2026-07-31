stations = [
    {"id": 1, "name": "Darmstadt Hbf", "city": "Darmstadt"},
    {"id": 2, "name": "Luisenplatz", "city": "Darmstadt"},
    {"id": 3, "name": "TU Lichtwiese", "city": "Darmstadt"},
    {"id": 4, "name": "Schloss", "city": "Darmstadt"},
    {"id": 5, "name": "Darmstadt Nord", "city": "Darmstadt"}
]


lines = [
    {"name": "Tram 2", "type": "tram"},
    {"name": "RB", "type": "train"}
]


trips = [
    {
        "id": 1,
        "line_name": "Tram 2",
        "destination": "TU Lichtwiese"
    },
    {
        "id": 2,
        "line_name": "Tram 2",
        "destination": "Darmstadt Hbf"
    },
    {
        "id": 3,
        "line_name": "RB",
        "destination": "Darmstadt Nord"
    }
]


trip_stops = [
    {"trip_id": 1, "station_id": 1, "stop_order": 1, "minute": 0},
    {"trip_id": 1, "station_id": 2, "stop_order": 2, "minute": 7},
    {"trip_id": 1, "station_id": 4, "stop_order": 3, "minute": 10},
    {"trip_id": 1, "station_id": 3, "stop_order": 4, "minute": 19},

    {"trip_id": 2, "station_id": 3, "stop_order": 1, "minute": 0},
    {"trip_id": 2, "station_id": 4, "stop_order": 2, "minute": 9},
    {"trip_id": 2, "station_id": 2, "stop_order": 3, "minute": 12},
    {"trip_id": 2, "station_id": 1, "stop_order": 4, "minute": 20},

    {"trip_id": 3, "station_id": 1, "stop_order": 1, "minute": 0},
    {"trip_id": 3, "station_id": 5, "stop_order": 2, "minute": 5}
]