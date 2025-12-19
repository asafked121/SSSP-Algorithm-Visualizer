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

import random
from typing import List, Sequence

from graph import Graph

# Example adjacency matrix for a weighted directed graph with nodes 0..4.
# Use float("inf") to indicate the absence of an edge.
NODES: Sequence[int] = (0, 1, 2, 3, 4)
ADJ_MATRIX: List[List[float]] = [
    [0.0, 1.0, 4.0, float("inf"), float("inf")],
    [float("inf"), 0.0, 2.0, 5.0, float("inf")],
    [float("inf"), float("inf"), 0.0, 1.0, 7.0],
    [float("inf"), float("inf"), float("inf"), 0.0, 3.0],
    [2.0, float("inf"), float("inf"), float("inf"), 0.0],
]


def build_graph_from_matrix(directed: bool = True) -> Graph:
    """Convert ADJ_MATRIX into a Graph instance."""
    g = Graph(directed=directed)
    for i, row in enumerate(ADJ_MATRIX):
        for j, weight in enumerate(row):
            if i == j:
                continue
            if weight != float("inf"):
                g.add_edge(NODES[i], NODES[j], weight)
    return g


def build_large_random_graph(
    num_nodes: int = 5000,
    avg_edges_per_node: int = 10,
    min_weight: float = 1.0,
    max_weight: float = 100.0,
    directed: bool = True,
    seed: int | None = None,
) -> Graph:
    """
    Generate a large random sparse graph.

    Args:
        num_nodes: Number of nodes in the graph (default 5000).
        avg_edges_per_node: Average number of outgoing edges per node (default 10).
        min_weight: Minimum edge weight (default 1.0).
        max_weight: Maximum edge weight (default 100.0).
        directed: Whether the graph is directed (default True).
        seed: Random seed for reproducibility (default None).

    Returns:
        A Graph instance with the specified properties.
    """
    if seed is not None:
        random.seed(seed)

    g = Graph(directed=directed)

    # Generate random edges
    total_edges = num_nodes * avg_edges_per_node
    edges_added = 0

    # Use a set to avoid duplicate edges
    existing_edges: set[tuple[int, int]] = set()

    while edges_added < total_edges:
        src = random.randint(0, num_nodes - 1)
        dst = random.randint(0, num_nodes - 1)

        # Skip self-loops and duplicate edges
        if src == dst or (src, dst) in existing_edges:
            continue

        weight = random.uniform(min_weight, max_weight)
        g.add_edge(src, dst, weight)
        existing_edges.add((src, dst))
        edges_added += 1

    return g


# Pre-built large graph with 5000 nodes (lazy loaded)
_large_graph_cache: Graph | None = None


def get_large_graph(seed: int = 42) -> Graph:
    """
    Get a large graph with 5000 nodes and ~50,000 edges.
    Uses caching to avoid regenerating on each call.
    """
    global _large_graph_cache
    if _large_graph_cache is None:
        print("Generating large graph with 5000 nodes...")
        _large_graph_cache = build_large_random_graph(
            num_nodes=5000,
            avg_edges_per_node=10,
            seed=seed,
        )
        print(f"Generated graph with {len(list(_large_graph_cache.nodes))} nodes and {_large_graph_cache.edge_count} edges")
    return _large_graph_cache
