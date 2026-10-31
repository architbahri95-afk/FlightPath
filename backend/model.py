"""Graph model for the flight network: airports are vertices, direct flights are
undirected weighted edges carrying three weights (distance, time, cost)."""
import math
import zlib

SPEED_KMH = 780        # average cruise speed used for flight time
TURNAROUND_MIN = 35    # fixed taxi/boarding overhead added to every leg
BASE_FARE = 1800       # fixed fare per leg (INR)
RATE_PER_KM = 4.2      # variable fare per km (INR)
MIN_MULT = 0.85        # fares vary 0.85x..1.25x per route (deterministic)

METRICS = ("distance", "time", "cost")


def haversine(lat1, lon1, lat2, lon2):
    """Great-circle distance in km."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def edge_attrs(a, b, dist):
    # crc32 (not hash()) so the "market price" of a route is stable across runs
    mult = MIN_MULT + (zlib.crc32("".join(sorted((a, b))).encode()) % 41) / 100
    return {
        "distance": dist,
        "time": dist / SPEED_KMH * 60 + TURNAROUND_MIN,
        "cost": BASE_FARE + dist * RATE_PER_KM * mult,
    }


class Graph:
    def __init__(self):
        self.airports = {}   # code -> {city, lat, lon}
        self.adj = {}        # code -> {neighbour: {distance, time, cost}}

    def add_airport(self, code, city, lat, lon):
        self.airports[code] = {"city": city, "lat": lat, "lon": lon}
        self.adj.setdefault(code, {})

    def add_route(self, a, b):
        pa, pb = self.airports[a], self.airports[b]
        attrs = edge_attrs(a, b, haversine(pa["lat"], pa["lon"], pb["lat"], pb["lon"]))
        self.adj[a][b] = attrs
        self.adj[b][a] = dict(attrs)

    def path_total(self, path, metric):
        return sum(self.adj[u][v][metric] for u, v in zip(path, path[1:]))

    def path_totals(self, path):
        return {m: self.path_total(path, m) for m in METRICS}

    def without(self, closed):
        """Copy of the graph with some airports closed (removed)."""
        g = Graph()
        for code, info in self.airports.items():
            if code not in closed:
                g.airports[code] = info
                g.adj[code] = {v: a for v, a in self.adj[code].items() if v not in closed}
        return g

    def undirected_edges(self):
        seen = set()
        for u, nbrs in self.adj.items():
            for v, a in nbrs.items():
                if (v, u) not in seen:
                    seen.add((u, v))
                    yield u, v, a

    @property
    def edge_count(self):
        return sum(len(n) for n in self.adj.values()) // 2
