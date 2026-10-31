import itertools
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

from algorithms import ALGORITHMS, bfs_min_stops, dijkstra, floyd_warshall, k_shortest  # noqa: E402
from data import build_network  # noqa: E402
from model import METRICS  # noqa: E402

G = build_network()
CODES = list(G.airports)


class Correctness(unittest.TestCase):
    def test_network_is_connected(self):
        for c in CODES:
            self.assertTrue(dijkstra(G, "DEL", c, "distance")["found"], c)

    def test_floyd_warshall_agrees_with_dijkstra(self):
        rnd = random.Random(1)
        for _ in range(40):
            s, t = rnd.sample(CODES, 2)
            for metric in METRICS:
                self.assertAlmostEqual(dijkstra(G, s, t, metric)["total"],
                                       floyd_warshall(G, s, t, metric)["total"], places=6)

    def test_bfs_has_fewest_hops(self):
        for s, t in itertools.permutations(CODES, 2):
            hops = len(bfs_min_stops(G, s, t, "cost")["path"])
            for name in ("dijkstra", "floyd_warshall"):
                self.assertLessEqual(hops, len(ALGORITHMS[name](G, s, t, "cost")["path"]))


class Features(unittest.TestCase):
    def test_k_shortest_sorted_distinct_simple(self):
        alts = k_shortest(G, "DEL", "TRV", "cost", 5)
        self.assertEqual(len(alts), 5)
        totals = [a["total"] for a in alts]
        self.assertEqual(totals, sorted(totals))
        paths = [tuple(a["path"]) for a in alts]
        self.assertEqual(len(set(paths)), len(paths))
        for p in paths:
            self.assertEqual(len(set(p)), len(p))

    def test_closed_airport_is_avoided(self):
        g = G.without({"BOM"})
        for name, fn in ALGORITHMS.items():
            self.assertNotIn("BOM", fn(g, "DEL", "GOI", "distance")["path"], name)

    def test_disconnected_returns_not_found(self):
        g = G.without({"DEL", "SXR"})            # Leh's only links are DEL and SXR
        self.assertEqual(g.adj["IXL"], {})
        for name, fn in ALGORITHMS.items():
            self.assertFalse(fn(g, "BOM", "IXL", "distance")["found"], name)


if __name__ == "__main__":
    unittest.main(verbosity=1)
