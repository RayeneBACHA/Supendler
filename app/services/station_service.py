from app.schemas.station import Station


class StationService:
    def __init__(self, stations: list[dict]):
        self.stations = stations

    def get_all(self):
        return self.stations

    def get_by_id(self, station_id: int):
        for station in self.stations:
            if station["id"] == station_id:
                return station

        return None

    def create(self, station: Station):
        new_station = {
            "id": self._get_next_id(),
            "name": station.name,
            "city": station.city
        }

        self.stations.append(new_station)
        return new_station

    def update(self, station_id: int, updated_station: Station):
        station = self.get_by_id(station_id)

        if station is None:
            return None

        station["name"] = updated_station.name
        station["city"] = updated_station.city

        return station

    def delete(self, station_id: int):
        station = self.get_by_id(station_id)

        if station is None:
            return None

        self.stations.remove(station)
        return station

    def _get_next_id(self):
        if len(self.stations) == 0:
            return 1

        highest_id = max(station["id"] for station in self.stations)
        return highest_id + 1