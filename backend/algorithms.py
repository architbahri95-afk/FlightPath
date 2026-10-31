"""Shortest-path algorithms for the flight route planner.

Every algorithm has the same signature  f(graph, src, dst, metric)  and returns
a dict with the path, its total weight and instrumentation (nodes expanded,
edge relaxations, wall time) so the algorithms can be compared empirically.
"""
import heapq
import time
from collections import deque

INF = float("inf")


def _pack(found, path, total, visited, relax, expanded, t0):
    return {
        "found": found,
        "path": path,
        "total": total if found else None,
        "visited": visited,
        "relaxations": relax,
        "expanded": expanded,
        "micros": round((time.perf_counter() - t0) * 1e6),
    }


def _rebuild(prev, t):
    path = [t]
    while prev[path[-1]] is not None:
        path.append(prev[path[-1]])
    return path[::-1]


# 1. Dijkstra -- greedy, binary heap.  O((V + E) log V)
def dijkstra(g, s, t, metric, banned_nodes=frozenset(), banned_edges=frozenset()):
    t0 = time.perf_counter()
    dist, prev = {s: 0.0}, {s: None}
    done, order, relax = set(), [], 0
    pq = [(0.0, s)]
    while pq:
        d, u = heapq.heappop(pq)
        if u in done:
            continue
        done.add(u)
        order.append(u)
        if u == t:
            break
        for v, a in g.adj[u].items():
            if v in banned_nodes or (u, v) in banned_edges:
                continue
            relax += 1
            nd = d + a[metric]
            if nd < dist.get(v, INF):
                dist[v], prev[v] = nd, u
                heapq.heappush(pq, (nd, v))
    if t not in done:
        return _pack(False, [], None, order, relax, len(done), t0)
    return _pack(True, _rebuild(prev, t), dist[t], order, relax, len(done), t0)


# 2. Floyd-Warshall -- all-pairs dynamic programming.  O(V^3)
def floyd_warshall(g, s, t, metric):
    t0 = time.perf_counter()
    nodes = list(g.adj)
    idx = {c: i for i, c in enumerate(nodes)}
    n = len(nodes)
    d = [[INF] * n for _ in range(n)]
    nxt = [[None] * n for _ in range(n)]
    for i in range(n):
        d[i][i], nxt[i][i] = 0.0, i
    for u in nodes:
        for v, a in g.adj[u].items():
            d[idx[u]][idx[v]], nxt[idx[u]][idx[v]] = a[metric], idx[v]
    ops = 0
    for k in range(n):
        dk = d[k]
        for i in range(n):
            di, dik = d[i], d[i][k]
            for j in range(n):
                nd = dik + dk[j]
                if nd < di[j]:
                    di[j], nxt[i][j] = nd, nxt[i][k]
            ops += n
    i, j = idx[s], idx[t]
    if d[i][j] == INF:
        return _pack(False, [], None, [], ops, n, t0)
    path = [s]
    while i != j:
        i = nxt[i][j]
        path.append(nodes[i])
    return _pack(True, path, d[idx[s]][j], list(path), ops, n, t0)


# 3. BFS -- fewest flights (ignores the weight, then reports it afterwards).
def bfs_min_stops(g, s, t, metric):
    t0 = time.perf_counter()
    prev, order, relax = {s: None}, [], 0
    q = deque([s])
    while q:
        u = q.popleft()
        order.append(u)
        if u == t:
            break
        for v in g.adj[u]:
            relax += 1
            if v not in prev:
                prev[v] = u
                q.append(v)
    if t not in prev:
        return _pack(False, [], None, order, relax, len(order), t0)
    path = _rebuild(prev, t)
    return _pack(True, path, g.path_total(path, metric), order, relax, len(order), t0)


ALGORITHMS = {
    "dijkstra": dijkstra,
    "floyd_warshall": floyd_warshall,
    "bfs": bfs_min_stops,
}

LABELS = {
    "dijkstra": "Dijkstra",
    "floyd_warshall": "Floyd-Warshall",
    "bfs": "BFS (fewest flights)",
}


# 4. Yen's algorithm -- the K best loop-free routes (alternatives).
def k_shortest(g, s, t, metric, k=3):
    first = dijkstra(g, s, t, metric)
    if not first["found"]:
        return []
    accepted = [first["path"]]
    candidates, queued = [], set()
    while len(accepted) < k:
        last = accepted[-1]
        for i in range(len(last) - 1):
            spur, root = last[i], last[: i + 1]
            banned_edges = {(p[i], p[i + 1]) for p in accepted
                            if len(p) > i + 1 and p[: i + 1] == root}
            r = dijkstra(g, spur, t, metric, set(root[:-1]), banned_edges)
            if r["found"]:
                full = tuple(root[:-1] + r["path"])
                if full not in queued and list(full) not in accepted:
                    queued.add(full)
                    heapq.heappush(candidates, (g.path_total(full, metric), full))
        if not candidates:
            break
        accepted.append(list(heapq.heappop(candidates)[1]))
    return [{"path": p, "total": g.path_total(p, metric)} for p in accepted]
