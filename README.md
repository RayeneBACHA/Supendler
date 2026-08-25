# SUPENDLER

**Smart multimodal routing for public transport, bikes, scooters, and walking.**

SUPENDLER is a multimodal routing engine that does more than compare travel times.

Its main idea is to identify **public-transport connections that become reachable when alternative mobility is used intelligently**.

For example:

```text
Ready to leave:       12:07
Tram departs:         12:18

Walk to stop:         25 min → miss the tram ❌
Bike to stop:         10 min → catch the tram ✅
```

The bike does not simply save 15 minutes of walking — it **unlocks an earlier public-transport connection**.

---

## Why SUPENDLER?

Traditional route planners mostly ask:

> What is the fastest route?

SUPENDLER additionally asks:

> Which public-transport journeys become reachable or meaningfully better because of the mobility options available to me?

The long-term goal is to combine:

```text
Walking
Folding bikes
Shared bikes
Shared scooters
Public transport
```

into complete, timetable-aware journeys.

---

## Current Features

### Direct mobility

SUPENDLER currently supports:

* Walking
* Folding bike
* Shared bike
* Shared scooter

Shared mobility includes basic feasibility checks such as:

* vehicle availability
* pickup permission
* drop-off permission
* walking distance to the vehicle
* scooter battery level

---

### Timetable-aware public transport

The routing engine currently supports:

* scheduled public-transport trips
* departure and arrival times
* stop ordering
* access-time feasibility
* catchable vs. missed departures
* `leave_by_time`
* `wait_before_start_minutes`
* mobility-unlocked departures

Example:

```text
Walking:
12:18 ❌
12:38 ✅

Bike:
12:18 ✅
12:38 ✅

Unlocked by bike:
12:18
```

---

### Multimodal PT profiles

Current public-transport profiles include:

```text
Walk → PT → Walk
```

```text
Folding Bike → PT → Folding Bike
```

```text
Shared Bike/Scooter → PT → Walk
```

```text
Walk → PT → Shared Bike/Scooter
```

Shared mobility is intentionally filtered more strictly than walking or a private bike.

For example, shared access can be included when it unlocks an otherwise unreachable PT departure.

Shared egress can be included when it improves the final arrival by at least the configured threshold.

---

### One-transfer routing

One-transfer public-transport routing is currently under development.

The first supported transfer model is:

```text
PT 1
→ same-stop walking transfer
→ PT 2
```

Current transfer logic already supports:

* finding possible transfer stops
* combining two scheduled trips
* checking timetable compatibility
* rejecting same-trip pseudo-transfers
* minimum same-stop transfer walking time
* filtering dominated transfers
* rejecting unnecessary transfers unless they provide a meaningful arrival-time improvement

The current implementation uses:

```text
same-stop transfer walk time = 1 minute
minimum useful arrival gain  = 5 minutes
```

---

## Routing Profiles

Current route profiles:

```text
direct_walk
direct_bike
direct_shared

pt_walk
pt_folding_bike
pt_shared
```

Routes use a common `legs[]` structure so the frontend can render multimodal journeys consistently.

Example:

```text
🚲 → 🚋 → 🚶
```

---

## Timetable Model

The internal timetable model has been refactored toward GTFS concepts:

```text
stops
routes
trips
stop_times
```

Example:

```text
Route
    ↓
Trip
    ↓
StopTime
    ↓
Stop
```

A `Trip` represents one concrete scheduled journey.

A `StopTime` contains information such as:

```text
trip_id
stop_id
stop_sequence
arrival_time
departure_time
```

This structure is designed to make migration to real GTFS data easier later.

---

## Tech Stack

* **Python**
* **FastAPI**
* **Pydantic**

Development currently uses manually controlled test data so routing behavior can be implemented and tested before introducing a large real-world timetable dataset.

---

## Running Locally

Clone the repository:

```bash
git clone https://github.com/<your-username>/supendler.git
cd supendler
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it.

### Windows

```powershell
venv\Scripts\activate
```

### Linux / macOS

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the FastAPI development server:

```bash
uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/docs
```

to use the automatically generated Swagger API documentation.

---

## Current Status

**Version 0.1 — active development**

The current focus is:

```text
one-transfer public-transport routing
```

The basic transfer search and dominance filtering are working.

The next milestone is to create and test a timetable scenario containing a genuinely useful transfer, then integrate transfer journeys into the main route-generation pipeline.

---

## Roadmap

### In progress

* [ ] Test a genuinely useful PT transfer
* [ ] Apply user `ready_time` to transfer journeys
* [ ] Integrate one-transfer routing into `RouteService`
* [ ] Represent transfer journeys using the common route response model

### Next

* [ ] Folding-bike transfers
* [ ] Shared-mobility transfers
* [ ] Nearby-stop transfers
* [ ] Mobility-unlocked transfers
* [ ] Real origin and destination coordinates
* [ ] Automatic walking/bike route distances

### Later

* [ ] Real GTFS timetable import
* [ ] Service calendars and exceptions
* [ ] Platform-aware transfers
* [ ] Real-time transit updates
* [ ] Live shared-mobility availability
* [ ] Database integration
* [ ] Preference-aware route ranking
* [ ] Frontend application

---

## Core Principle

SUPENDLER is built around one question:

> **Which complete public-transport journeys become reachable or meaningfully better when I intelligently use the mobility options available to me?**

That principle guides the routing engine, timetable model, transfer logic, mobility filtering, and future frontend.
