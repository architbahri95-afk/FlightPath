"""Empirical complexity study on random networks of growing size."""
import random

from algorithms import ALGORITHMS
from model import Graph


def random_graph(n, seed=7):
    rnd = random.Random(seed)
    g = Graph()
    for i in range(n):
        g.add_airport(f"N{i}", f"Node {i}", rnd.uniform(8, 34), rnd.uniform(68, 96))
    codes = list(g.airports)
    for i in range(n):                       # ring keeps the graph connected
        g.add_route(codes[i], codes[(i + 1) % n])
    for _ in range(2 * n):                   # then ~2n random chords
        a, b = rnd.sample(codes, 2)
        if b not in g.adj[a]:
            g.add_route(a, b)
    return g


def run_benchmark(sizes=(10, 20, 40, 60, 80, 100), metric="distance", queries=15):
    """Average over several random origin/destination pairs per size, so one
    lucky (adjacent) pair cannot distort the curve."""
    rows = []
    for n in sizes:
        g = random_graph(n)
        rnd = random.Random(n)
        pairs = [rnd.sample(list(g.airports), 2) for _ in range(queries)]
        res = {}
        for name, fn in ALGORITHMS.items():
            runs = [fn(g, s, t, metric) for s, t in pairs]
            res[name] = {"relaxations": round(sum(r["relaxations"] for r in runs) / queries),
                         "micros": round(sum(r["micros"] for r in runs) / queries)}
        rows.append({"n": n, "edges": g.edge_count, "results": res})
    return rows
