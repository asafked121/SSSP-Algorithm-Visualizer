# SSSP Algorithm Visualizer - A visualization and benchmarking tool for SSSP algorithms.
# Copyright (C) 2025  Asaf Kedar
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Dict

sys.path.append(str(Path(__file__).parent / "src"))

from algorithms.dijkstra import dijkstra  # noqa: E402
from algorithms.sorting_barrier_sssp import SortingBarrierSSSP  # noqa: E402
from graph import Graph  # noqa: E402


def load_graph(path: Path, directed: bool) -> Graph:
    with path.open() as handle:
        return Graph.from_edge_list(handle, directed=directed)


def format_distances(dist: Dict[int, float]) -> str:
    items = sorted(dist.items(), key=lambda kv: kv[0])
    return ", ".join(
        f"{node}:{d:.3f}" if d < float("inf") else f"{node}:∞" for node, d in items
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="SSSP comparison: Dijkstra vs. sorting-barrier algorithm.")
    parser.add_argument("graph_file", type=Path, help="Path to an edge list file: 'u v [weight]' per line.")
    parser.add_argument("--undirected", action="store_true", help="Treat the graph as undirected (default: directed).")
    parser.add_argument("--source", type=int, help="Source vertex id (default: smallest id in the graph).")
    parser.add_argument(
        "--show-distances",
        action="store_true",
        help="Print distance maps (only recommended for small graphs).",
    )
    args = parser.parse_args()

    graph = load_graph(args.graph_file, directed=not args.undirected)
    if not graph.nodes:
        raise SystemExit("Graph is empty.")

    source = args.source if args.source is not None else min(graph.nodes)

    dijkstra_start = time.perf_counter()
    dij_dist, _ = dijkstra(graph, source)
    dijkstra_time = time.perf_counter() - dijkstra_start

    sb = SortingBarrierSSSP(graph)
    sb_start = time.perf_counter()
    sb_dist, _ = sb.run(source)
    sb_time = time.perf_counter() - sb_start

    print(f"Graph: {len(graph.nodes)} vertices, {graph.edge_count} edges, source={source}")
    print(f"Dijkstra: {dijkstra_time * 1000:.2f} ms")
    print(f"Sorting-barrier: {sb_time * 1000:.2f} ms")

    disagreement = [
        (node, dij_dist[node], sb_dist[node])
        for node in graph.nodes
        if abs(dij_dist[node] - sb_dist[node]) > 1e-9
    ]
    if disagreement:
        print(f"Warning: distances differ for {len(disagreement)} vertices.")
    else:
        print("Distances match between algorithms.")

    if args.show_distances:
        print("Dijkstra distances:")
        print(format_distances(dij_dist))
        print("Sorting-barrier distances:")
        print(format_distances(sb_dist))


if __name__ == "__main__":
    main()
