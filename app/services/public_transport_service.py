class PublicTransportService:
    def __init__(
        self,
        stations: list[dict],
        lines: list[dict],
        trips: list[dict],
        trip_stops: list[dict]
    ):
        self.stations = stations
        self.lines = lines
        self.trips = trips
        self.trip_stops = trip_stops

    def get_all_trips(self):
        return self.trips

    def get_station_by_id(self, station_id: int):
        for station in self.stations:
            if station["id"] == station_id:
                return station

        return None

    def get_line_by_name(self, line_name: str):
        for line in self.lines:
            if line["name"] == line_name:
                return line

        return None

    def get_trip_by_id(self, trip_id: int):
        for trip in self.trips:
            if trip["id"] == trip_id:
                return trip

        return None

    def get_stops_for_trip(self, trip_id: int):
        stops = []

        for stop in self.trip_stops:
            if stop["trip_id"] == trip_id:
                stops.append(stop)

        return sorted(stops, key=lambda stop: stop["stop_order"])

    def get_trips_for_station(self, station_id: int):
        result = []

        for stop in self.trip_stops:
            if stop["station_id"] == station_id:
                trip = self.get_trip_by_id(stop["trip_id"])
                line = self.get_line_by_name(trip["line_name"])

                result.append({
                    "trip_id": trip["id"],
                    "line": line["name"],
                    "line_type": line["type"],
                    "destination": trip["destination"],
                    "stop_order": stop["stop_order"],
                    "minute": stop["minute"]
                })

        return result

    def find_direct_trips(self, from_station_id: int, to_station_id: int):
        direct_trips = []

        for trip in self.trips:
            stops = self.get_stops_for_trip(trip["id"])

            from_stop = None
            to_stop = None

            for stop in stops:
                if stop["station_id"] == from_station_id:
                    from_stop = stop

                if stop["station_id"] == to_station_id:
                    to_stop = stop

            if from_stop is None or to_stop is None:
                continue

            if from_stop["stop_order"] >= to_stop["stop_order"]:
                continue

            line = self.get_line_by_name(trip["line_name"])

            stops_between = []

            for stop in stops:
                if from_stop["stop_order"] <= stop["stop_order"] <= to_stop["stop_order"]:
                    station = self.get_station_by_id(stop["station_id"])

                    stops_between.append({
                        "station_id": station["id"],
                        "station_name": station["name"],
                        "stop_order": stop["stop_order"],
                        "minute": stop["minute"]
                    })

            duration_minutes = to_stop["minute"] - from_stop["minute"]

            direct_trips.append({
                "trip_id": trip["id"],
                "line": line["name"],
                "line_type": line["type"],
                "destination": trip["destination"],
                "from_station_id": from_station_id,
                "to_station_id": to_station_id,
                "duration_minutes": duration_minutes,
                "stops": stops_between
            })

        return direct_trips