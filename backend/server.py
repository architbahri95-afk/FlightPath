"""HTTP server (standard library only): JSON API + static frontend.

    python server.py            ->  http://localhost:8000
"""
import json
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from algorithms import ALGORITHMS, LABELS, k_shortest
from benchmark import run_benchmark
from data import build_network
from model import METRICS

FRONTEND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
NETWORK = build_network()


class ApiError(Exception):
    pass


def r1(x):
    return None if x is None else round(x, 1)


def itinerary(g, path):
    legs = []
    for u, v in zip(path, path[1:]):
        a = g.adj[u][v]
        legs.append({
            "from": u, "to": v,
            "from_city": g.airports[u]["city"], "to_city": g.airports[v]["city"],
            "distance": r1(a["distance"]), "time": r1(a["time"]), "cost": r1(a["cost"]),
        })
    return {"legs": legs, "totals": {m: r1(t) for m, t in g.path_totals(path).items()}}


def parse_query(q):
    def one(name, default=None):
        return q.get(name, [default])[0]

    src, dst = (one("src") or "").upper(), (one("dst") or "").upper()
    metric = one("metric", "distance")
    avoid = {c for c in (one("avoid", "") or "").upper().split(",") if c}
    if src not in NETWORK.airports or dst not in NETWORK.airports:
        raise ApiError("Unknown airport code.")
    if metric not in METRICS:
        raise ApiError("metric must be distance, time or cost.")
    if not avoid <= set(NETWORK.airports):
        raise ApiError("Unknown airport in avoid list.")
    if src in avoid or dst in avoid:
        raise ApiError("The origin or destination airport is closed.")
    if src == dst:
        raise ApiError("Choose two different airports.")
    return src, dst, metric, NETWORK.without(avoid), q


def route(q):
    src, dst, metric, g, q = parse_query(q)
    algo = q.get("algo", ["dijkstra"])[0]
    if algo not in ALGORITHMS:
        raise ApiError("Unknown algorithm.")
    k = max(1, min(5, int(q.get("k", ["3"])[0])))
    r = ALGORITHMS[algo](g, src, dst, metric)
    out = {"algo": algo, "label": LABELS[algo], "metric": metric, "found": r["found"],
           "path": r["path"], "total": r1(r["total"]), "visited": r["visited"],
           "stats": {"expanded": r["expanded"], "relaxations": r["relaxations"], "micros": r["micros"]}}
    if r["found"]:
        out["itinerary"] = itinerary(g, r["path"])
        out["alternatives"] = [
            {"path": a["path"], "total": r1(a["total"]), "itinerary": itinerary(g, a["path"])}
            for a in k_shortest(g, src, dst, metric, k)
        ]
    return out


def compare(q):
    src, dst, metric, g, _ = parse_query(q)
    rows = []
    for name, fn in ALGORITHMS.items():
        r = fn(g, src, dst, metric)
        rows.append({"algo": name, "label": LABELS[name], "found": r["found"],
                     "total": r1(r["total"]), "hops": max(len(r["path"]) - 1, 0),
                     "expanded": r["expanded"], "relaxations": r["relaxations"],
                     "micros": r["micros"]})
    return rows


def network(_q):
    return {
        "airports": [{"code": c, **info} for c, info in NETWORK.airports.items()],
        "routes": [{"from": u, "to": v, "distance": r1(a["distance"]),
                    "time": r1(a["time"]), "cost": r1(a["cost"])}
                   for u, v, a in NETWORK.undirected_edges()],
    }


ENDPOINTS = {
    "/api/network": network,
    "/api/route": route,
    "/api/compare": compare,
    "/api/benchmark": lambda q: run_benchmark(),
}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=FRONTEND, **kw)

    def do_GET(self):
        u = urlparse(self.path)
        if not u.path.startswith("/api/"):
            return super().do_GET()
        fn = ENDPOINTS.get(u.path)
        try:
            if fn is None:
                self.send_json({"error": "Not found"}, 404)
            else:
                self.send_json(fn(parse_qs(u.query)))
        except ApiError as e:
            self.send_json({"error": str(e)}, 400)
        except ValueError:
            self.send_json({"error": "Bad parameter"}, 400)

    def send_json(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        sys.stderr.write("[api] " + fmt % args + "\n")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"FlightPath running on http://localhost:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
