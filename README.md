# FlightPath

A full-stack flight route planner that finds the shortest, fastest or cheapest itinerary
between 28 Indian airports, animates how each algorithm searches, lists alternative routes,
and measures how the algorithms scale. Built as a Design and Analysis of Algorithms (DAA) project.

- **Backend:** Python 3, standard library only (no `pip install`)
- **Frontend:** plain HTML, CSS and JavaScript (SVG map, no libraries)

## Quick start

```bash
git clone https://github.com/<your-username>/FlightPath.git
cd FlightPath
python backend/server.py        # use `py backend/server.py` on Windows if needed
```

Open http://localhost:8000. Set `PORT=9000` to use another port.

Run the tests from the repository root:

```bash
python -m unittest discover tests -v
```

## Project structure

```
FlightPath/
├── backend/
│   ├── algorithms.py    Dijkstra, Floyd-Warshall, BFS, Yen's K-shortest
│   ├── benchmark.py     Empirical complexity study on random graphs
│   ├── data.py          28 airports and ~85 direct routes
│   ├── model.py         Graph class, haversine distance, edge weights
│   └── server.py        HTTP server, JSON API and static file serving
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
├── tests/
│   └── test_algorithms.py
├── .gitignore
├── LICENSE
└── README.md
```

## API

| Endpoint | Purpose |
|---|---|
| `GET /api/network` | Airports and routes |
| `GET /api/route?src=DEL&dst=TRV&metric=cost&algo=dijkstra&k=3&avoid=BOM,BLR` | Best route, search order, itinerary, K alternatives |
| `GET /api/compare?src=..&dst=..&metric=..&avoid=..` | Every algorithm on the same query |
| `GET /api/benchmark` | Operation counts on random graphs of 10 to 100 airports |

`metric` is `distance`, `time` or `cost`. `algo` is `dijkstra`, `floyd_warshall` or `bfs`.
`avoid` is a comma-separated list of closed airports.

## Problem model

- Vertices are airports. Edges are direct flights, undirected, with three non-negative weights.
- Distance = great-circle (haversine) km.
- Time = distance / 780 km/h + 35 min taxi and boarding per leg, so extra stops cost time.
- Fare = Rs 1800 + Rs 4.2/km x a per-route factor between 0.85 and 1.25, so extra stops cost money.

## Algorithms and complexity

| Algorithm | Paradigm | Time | Space | Role |
|---|---|---|---|---|
| Dijkstra | Greedy + binary heap | O((V+E) log V) | O(V) | Default single-pair search |
| Floyd-Warshall | Dynamic programming | O(V^3) | O(V^2) | All pairs |
| BFS | Traversal | O(V+E) | O(V) | Fewest flights only |
| Yen's K-shortest | Repeated Dijkstra | O(K.V.(E+V log V)) | O(K.V) | Alternative routes shown under each result |

**Why Dijkstra is correct here:** all weights are positive, so the greedy choice of the closest
unsettled vertex is safe. When a vertex is popped, its distance is final.

**Why BFS differs:** it minimises the number of edges, not the weight, so its result can cost more.
The compare table shows the percentage difference.

**Floyd-Warshall:** computes every pair at once. It is a poor fit for a single query but useful for
a lookup table.

## Features

- Closed airports: the graph is copied without those vertices, so every algorithm handles disruptions unchanged.
- Yen's algorithm: each iteration removes one edge of a known path and the root-path nodes, then reruns Dijkstra from the spur node.
- Instrumentation: each algorithm reports nodes expanded, edge relaxations and microseconds.
- Testing: Dijkstra and Floyd-Warshall must agree on every metric, and BFS must never use more flights. Alternative routes must be distinct, sorted and loop-free.

## Ideas for extension

- Load real route data from a CSV.
- Layover constraints such as maximum stops or minimum connection time.
- Multi-objective search (Pareto front of cost vs time).
- Time-dependent edges for real timetables.

## License

MIT, see [LICENSE](LICENSE).
