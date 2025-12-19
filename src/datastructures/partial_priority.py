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
from typing import Dict, Iterable, List, Tuple


class PartialPriority:
    """
    A simplified version of the partial sorting structure from Duan et al.
    It supports:
    - insert(key, value): keep the smallest value per key
    - batch_prepend(pairs): insert many (key, value) pairs that are known to be
      smaller than current contents (modeled as regular inserts here)
    - pull(): remove up to M pairs with the smallest values and return them with
      a boundary separating them from the remaining elements.
    """

    def __init__(self, limit: int, upper_bound: float) -> None:
        self.limit = max(1, limit)
        self.upper_bound = upper_bound
        self._heap: List[Tuple[float, int]] = []
        self._best: Dict[int, float] = {}

    def insert(self, key: int, value: float) -> None:
        if value >= self.upper_bound:
            return
        best = self._best.get(key)
        if best is None or value < best:
            self._best[key] = value
            heapq.heappush(self._heap, (value, key))

    def batch_prepend(self, pairs: Iterable[Tuple[int, float]]) -> None:
        for key, value in pairs:
            self.insert(key, value)

    def pull(self) -> Tuple[float, List[int]]:
        """
        Returns (boundary, keys), where `keys` are up to `limit` items with
        smallest values, removed from the structure, and `boundary` separates
        returned keys from the rest (or upper_bound if empty).
        """
        keys: List[int] = []
        while self._heap and len(keys) < self.limit:
            value, key = heapq.heappop(self._heap)
            if self._best.get(key) != value:
                continue
            keys.append(key)
            del self._best[key]

        if not keys:
            return self.upper_bound, keys

        next_boundary = self.upper_bound
        while self._heap:
            value, key = self._heap[0]
            if self._best.get(key) != value:
                heapq.heappop(self._heap)
                continue
            next_boundary = value
            break

        return next_boundary, keys

    def is_empty(self) -> bool:
        return not self._best
