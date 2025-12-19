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

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class Edge:
    target: int
    weight: float


class Graph:
    def __init__(self, directed: bool = True) -> None:
        self.directed = directed
        self._adjacency: Dict[int, List[Edge]] = defaultdict(list)
        self._nodes: set[int] = set()

    @property
    def nodes(self) -> Iterable[int]:
        return self._nodes

    @property
    def edge_count(self) -> int:
        return sum(len(neighbors) for neighbors in self._adjacency.values())

    def add_edge(self, u: int, v: int, weight: float) -> None:
        if weight < 0:
            raise ValueError("Edge weights must be non-negative.")

        self._nodes.add(u)
        self._nodes.add(v)
        self._adjacency[u].append(Edge(v, weight))

        if not self.directed:
            self._adjacency[v].append(Edge(u, weight))

    def neighbors(self, u: int) -> Iterable[Edge]:
        return self._adjacency.get(u, [])

    @classmethod
    def from_edge_list(
        cls, lines: Iterable[str], directed: bool = True
    ) -> "Graph":
        """
        Build a graph from an iterable of strings, where each non-empty line is
        formatted as: u v [weight]
        Weight defaults to 1.0 if omitted.
        """
        graph = cls(directed=directed)
        for lineno, raw in enumerate(lines, start=1):
            text = raw.strip()
            if not text or text.startswith("#"):
                continue

            parts = text.split()
            if len(parts) not in (2, 3):
                raise ValueError(
                    f"Line {lineno}: expected 'u v [weight]' format, got '{text}'"
                )

            u, v = int(parts[0]), int(parts[1])
            weight = float(parts[2]) if len(parts) == 3 else 1.0
            graph.add_edge(u, v, weight)
        return graph
