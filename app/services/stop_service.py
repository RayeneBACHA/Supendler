from app.schemas.stop import Stop


class StopService:
    def __init__(self, stops: list[dict]):
        self.stops = stops

    def get_all(self):
        return self.stops

    def get_by_id(self, stop_id: int):
        for stop in self.stops:
            if stop["id"] == stop_id:
                return stop

        return None

    def create(self, stop: Stop):
        new_stop = {
            "stop_id": self._get_next_id(),
            "stop_name": stop.name,
            "city": stop.city
        }

        self.stops.append(new_stop)
        return new_stop

    def update(self, stop_id: int, updated_stop: Stop):
        stop = self.get_by_id(stop_id)

        if stop is None:
            return None

        stop["stop_name"] = updated_stop.name
        stop["city"] = updated_stop.city

        return stop

    def delete(self, stop_id: int):
        stop = self.get_by_id(stop_id)

        if stop is None:
            return None

        self.stops.remove(stop)
        return stop

    def _get_next_id(self):
        if len(self.stops) == 0:
            return 1

        highest_id = max(stop["id"] for stop in self.stops)
        return highest_id + 1