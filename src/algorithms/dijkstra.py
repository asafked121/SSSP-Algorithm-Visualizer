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

import heapq
from typing import Dict, Tuple

from graph import Graph


def dijkstra(graph: Graph, source: int) -> Tuple[Dict[int, float], Dict[int, int | None]]:
    """
    Standard Dijkstra's algorithm using a binary heap.
    Returns distance map and predecessor map.
    """
    dist: Dict[int, float] = {node: float("inf") for node in graph.nodes}
    prev: Dict[int, int | None] = {node: None for node in graph.nodes}
    dist[source] = 0.0

    heap: list[tuple[float, int]] = [(0.0, source)]

    while heap:
        d_u, u = heapq.heappop(heap)
        if d_u != dist[u]:
            continue

        for edge in graph.neighbors(u):
            alt = d_u + edge.weight
            if alt < dist[edge.target]:
                dist[edge.target] = alt
                prev[edge.target] = u
                heapq.heappush(heap, (alt, edge.target))

    return dist, prev
