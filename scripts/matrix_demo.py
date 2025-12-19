from __future__ import annotations

import time

from data.adjacency_matrix import build_large_random_graph
from algorithms.dijkstra import dijkstra
from algorithms.sorting_barrier_sssp import SortingBarrierSSSP


def main() -> None:
    n = 5000
    avg_degree = 3  # Sparse: O(n) edges, not O(n²)
    g = build_large_random_graph(num_nodes=n, avg_edges_per_node=avg_degree, directed=True, seed=42)
    source = min(g.nodes)

    num_edges = g.edge_count
    max_possible_edges = n * (n - 1)  # For directed graph without self-loops
    density = num_edges / max_possible_edges
    print(f"Graph: {n} vertices, {num_edges} edges (avg degree: {avg_degree})")
    print(f"Density: {density:.6f} ({density * 100:.4f}%) — sparse graph")

    # Dijkstra
    d_start = time.perf_counter()
    d_dist, _ = dijkstra(g, source)
    d_time = time.perf_counter() - d_start
    #print(f"Dijkstra distances: {d_dist}")
    print(f"Dijkstra time: {d_time * 1000:.3f} ms")

    # Sorting-barrier
    sb = SortingBarrierSSSP(g)
    sb_start = time.perf_counter()
    try:
        sb_dist, _ = sb.run(source)
    except RuntimeError as exc:
        sb_time = time.perf_counter() - sb_start
        print(f"Sorting-barrier failed: {exc}")
        print(f"Sorting-barrier time before failure: {sb_time * 1000:.3f} ms")
        return
    sb_time = time.perf_counter() - sb_start
    #print(f"Sorting-barrier distances: {sb_dist}")
    print(f"Sorting-barrier time: {sb_time * 1000:.3f} ms")

    match = all(abs(d_dist[v] - sb_dist[v]) < 1e-9 for v in g.nodes)
    print("Match:", match)
    if d_time and sb_time and d_time > 0:
        ratio = sb_time / d_time
        print(f"Time ratio (sorting-barrier / dijkstra): {ratio:.3f}x")


if __name__ == "__main__":
    main()
