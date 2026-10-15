import { useState } from "react";

const STOPS = [
  { id: 1, name: "Darmstadt Hbf" },
  { id: 2, name: "Luisenplatz" },
  { id: 3, name: "TU Lichtwiese" },
  { id: 4, name: "Schloss" },
  { id: 5, name: "Darmstadt Nord" },
  { id: 6, name: "Rhein/Neckarstraße" }
];

function RouteSearchForm() {
  const [fromStopId, setFromStopId] = useState("");
  const [toStopId, setToStopId] = useState("");
  const [readyTime, setReadyTime] = useState("");
  const [hasFoldingBike, setHasFoldingBike] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();

    const requestData = {
      journey: {
        ready_time: readyTime
      },

      stop_pair: {
        start_stop_id: Number(fromStopId),
        end_stop_id: Number(toStopId)
      },

      user: {
        has_folding_bike: hasFoldingBike
      },

      direct: {
        walk_distance_km: 5,
        folding_bike_distance_km: 4.8
      },

      access: {
        walk_distance_km: 1.666667,
        folding_bike_distance_km: 1.5
      },

      egress: {
        walk_distance_km: 0.5,
        folding_bike_distance_km: 0.5
      }
    };

    const response = await fetch(
      "http://localhost:8008/route_options",
      {
        method: "POST",

        headers: {
          "Content-Type": "application/json"
        },

        body: JSON.stringify(requestData)
      }
    );

    const data = await response.json();

    console.log(data);
  }

  return (
    <form onSubmit={handleSubmit}>
      <label>
        From

        <select
          value={fromStopId}
          onChange={(event) => {
            setFromStopId(event.target.value);
          }}
        >
          <option value="">Choose a stop</option>

          {STOPS.map((stop) => (
            <option
              key={stop.id}
              value={stop.id}
            >
              {stop.name}
            </option>
          ))}
        </select>
      </label>

      <label>
        To

        <select
          value={toStopId}
          onChange={(event) => {
            setToStopId(event.target.value);
          }}
        >
          <option value="">Choose a stop</option>

          {STOPS.map((stop) => (
            <option
              key={stop.id}
              value={stop.id}
            >
              {stop.name}
            </option>
          ))}
        </select>
      </label>

      <label>
        Ready at

        <input
          type="time"
          value={readyTime}
          onChange={(event) => {
            setReadyTime(event.target.value);
          }}
        />
      </label>

      <label>
        <input
          type="checkbox"
          checked={hasFoldingBike}
          onChange={(event) => {
            setHasFoldingBike(event.target.checked);
          }}
        />

        I have a folding bike
      </label>

      <button type="submit">
        Find routes
      </button>
    </form>
  );
}

export default RouteSearchForm;