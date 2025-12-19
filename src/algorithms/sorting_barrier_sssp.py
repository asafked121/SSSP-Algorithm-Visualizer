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

"""
Sorting Barrier SSSP Algorithm.

Based on "Breaking the Sorting Barrier for Directed Single-Source Shortest Paths"
by Ran Duan, Jiayi Mao, Xiao Mao, Xinkai Shu, and Longhui Yin (arXiv:2504.17033v2).

Key parameters:
- k = log^{1/3}(n): Controls branching and pivot threshold
- t = log^{2/3}(n): Controls block size growth
- Recursion depth = log(n)/t = log^{1/3}(n) levels
"""

from __future__ import annotations

import heapq
import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple, Iterator

from datastructures.partial_sort import PartialSort
from graph import Graph, Edge


# =============================================================================
# DEBUG MODE CONFIGURATION
# =============================================================================
# Set to False to disable all safety checks for better performance.
# Set to True to enable safety checks that detect infinite loops and
# runaway recursion.
# =============================================================================
DEBUG_MODE = False


@dataclass
class BMSSPResult:
    """Result of a bounded multi-source shortest path computation.
    Args:
        boundary: Distance boundary achieved (tuple: (dist, node_id))
        complete: Vertices with finalized distances < boundary
    """
    boundary: Tuple[float, int]
    complete: Set[int]

class SortingBarrierSSSP:
    """
    Sorting Barrier SSSP Algorithm.

    """

    def __init__(self, graph: Graph) -> None:
        """
        Initialize the Sorting Barrier SSSP Algorithm.
        Args:
            graph: Graph to compute shortest paths on
        """
        self.graph = graph
        n = max(2, len(graph.nodes))
        log_n = math.log2(n)
        
        # Core parameters from the paper
        # k = log^{1/3}(n): branching factor and pivot threshold
        self.k = max(2, int(math.ceil(log_n ** (1 / 3))))
        # t = log^{2/3}(n): controls block size doubling rate
        self.t = max(1, int(math.ceil(log_n ** (2 / 3))))
        
        # Maximum recursion depth = log(n) / t = log^{1/3}(n)
        self.max_level = max(1, int(math.ceil(log_n / self.t)))
        
        # Safety budget to prevent runaway recursion or infinite loops
        # Only used when DEBUG_MODE is enabled
        if DEBUG_MODE:
            m = graph.edge_count
            self.safety_budget = max(10000, int(m * (log_n ** (2/3)) * 100))
            self._remaining_budget = self.safety_budget
        
        # Distance estimates (bd = bounded distance)
        self.bd: Dict[int, float] = {}
        # Predecessor map for path reconstruction
        self.pred: Dict[int, Optional[int]] = {}
        
        # Track which vertices have finalized distances
        self._finalized: Set[int] = set()
        
        # Precompute adjacency for efficient access
        self._adj: Dict[int, List[Edge]] = defaultdict(list)
        for node in graph.nodes:
            self._adj[node] = list(graph.neighbors(node))

    def run(self, source: int) -> Tuple[Dict[int, float], Dict[int, Optional[int]]]:
        """
        Compute single-source shortest paths from the given source.
        
        Returns:
            (distances, predecessors) where:
            - distances[v] = shortest path distance from source to v
            - predecessors[v] = previous vertex on shortest path to v
        """
        # Initialize all distances to infinity
        for node in self.graph.nodes:
            self.bd[node] = float("inf")
            self.pred[node] = None
        
        # Source initialization
        self.bd[source] = 0.0
        self.pred[source] = None
        
        # Reset safety budget for this run (only in debug mode)
        if DEBUG_MODE:
            self._remaining_budget = self.safety_budget
        
        # Run the bounded multi-source shortest path algorithm
        # Starting with source as the only active vertex
        self._bmssp(
            level=self.max_level,
            upper_bound=(float("inf"), 0),
            sources={source}
        )
        
        return self.bd, self.pred

    def _bmssp(
        self,
        level: int,
        upper_bound: Tuple[float, int],
        sources: Set[int]
    ) -> BMSSPResult:
        """
        Bounded Multi-Source Shortest Path (BMSSP) - Algorithm 3 from paper.
        
        Recursively computes shortest paths from multiple sources within
        a distance bound. This is the core of the algorithm.
        
        Args:
            level: Current recursion level (decreases toward 0)
            upper_bound: B - only process distances < upper_bound (tuple comparison)
            sources: Set of source vertices S (already have valid bd values)
        
        Returns:
            BMSSPResult with boundary B' and set of complete vertices U
        
        Raises:
            RuntimeError: If safety budget is exceeded (possible infinite loop)
        """
        # Safety check to prevent runaway execution (only in debug mode)
        if DEBUG_MODE:
            self._remaining_budget -= 1
            if self._remaining_budget <= 0:
                raise RuntimeError(
                    f"Safety budget exceeded ({self.safety_budget} operations). "
                    f"Possible infinite loop or unexpectedly large computation. "
                    f"Graph size: n={len(list(self.graph.nodes))}, m={self.graph.edge_count}"
                )
        
        if not sources:
            return BMSSPResult(boundary=upper_bound, complete=set())
        
        # Line 2-3: Base case (l = 0)
        if level == 0:
            return self._base_case(upper_bound, sources)
        
        # Line 4: Find pivots P and frontier W
        # Note: _find_pivots uses scalar distance internally for approximation, which is fine
        # But we pass tuple upper_bound for strict cutoff
        pivots, frontier = self._find_pivots(upper_bound, sources)
        
        # Line 5: Initialize D with M = 2^{(l-1)t}
        block_size = 2 ** ((level - 1) * self.t)
        block_size = max(1, min(block_size, len(self.graph.nodes)))
        
        queue = PartialSort(upper_bound=upper_bound[0], block_size=block_size)
        
        # Line 6: Insert pivots into D
        for p in pivots:
            if (self.bd[p], p) < upper_bound:
                queue.insert(p, self.bd[p])
        
        # Line 7: i ← 0; B_0' ← min_{x∈P} d̂[x]; U ← ∅
        # If P = ∅, set B_0' ← B
        if pivots:
            # Min tuple (dist, node_id)
            pivot_vals = [(self.bd[p], p) for p in pivots if self.bd[p] < float("inf")]
            B_prev = min(pivot_vals) if pivot_vals else upper_bound
        else:
            B_prev = upper_bound
        
        complete: Set[int] = set()  # U in paper
        
        # Maximum vertices to complete at this level: k * 2^{lt} (Line 8 condition)
        max_complete = self.k * (2 ** (level * self.t))
        
        # Safety tracking (only in debug mode)
        if DEBUG_MODE:
            loop_iterations = 0
            n = len(list(self.graph.nodes))
            max_loop_iterations = max(n * n, 10000)
        
        # Track the last B_i' for final return
        last_B_prime = B_prev
        
        # Line 8: while |U| < k·2^{lt} and D is non-empty
        while len(complete) < max_complete and not queue.is_empty():
            # Safety check for main loop (only in debug mode)
            if DEBUG_MODE:
                loop_iterations += 1
                if loop_iterations > max_loop_iterations:
                    raise RuntimeError(
                        f"Main loop exceeded {max_loop_iterations} iterations. "
                        "Possible infinite loop detected."
                    )
            
            # Line 10: B_i, S_i ← D.Pull()
            # B_i is now a tuple (priority, key)
            B_i, S_i = queue.pull()
            
            if not S_i:
                break
            
            # Filter out already completed vertices
            S_i = {v for v in S_i if v not in complete}
            if not S_i:
                continue
            
            # Line 11: B_i', U_i ← BMSSP(l-1, B_i, S_i)
            # Pass B_i (tuple) as upper bound
            result = self._bmssp(level - 1, B_i, S_i)
            B_i_prime = result.boundary
            U_i = result.complete
            
            # Line 12: U ← U ∪ U_i
            complete.update(U_i)
            
            # Track last B_i' for return value
            last_B_prime = B_i_prime
            
            # Line 13: K ← ∅
            K: List[Tuple[int, float]] = []
            
            # Lines 14-20: Process edges from U_i
            for u in U_i:
                dist_u = self.bd[u]
                for edge in self._adj.get(u, []):
                    v = edge.target
                    new_dist = dist_u + edge.weight
                    
                    # Line 15: if d̂[u] + w_uv ≤ d̂[v] then relaxation
                    if new_dist <= self.bd.get(v, float("inf")):
                        # Line 16: d̂[v] ← d̂[u] + w_uv
                        if new_dist < self.bd.get(v, float("inf")):
                            self.bd[v] = new_dist
                            self.pred[v] = u
                        
                        # Skip if already completed
                        if v in complete:
                            continue
                        
                        # Use tuple comparison for ranges
                        dist_tuple = (new_dist, v)
                        
                        # Line 17-18: if d̂[u] + w_uv ∈ [B_i, B) then D.Insert
                        # Comparison: B_i <= dist < upper_bound
                        if B_i <= dist_tuple < upper_bound:
                            queue.insert(v, new_dist)
                        # Line 19-20: else if d̂[u] + w_uv ∈ [B_i', B_i) then K ← K ∪ {v}
                        # Comparison: B_i_prime <= dist < B_i
                        elif B_i_prime <= dist_tuple < B_i:
                            K.append((v, new_dist))
            
            # Line 21: D.BatchPrepend(K ∪ {x ∈ S_i : d̂[x] ∈ [B_i', B_i)})
            # Add elements from S_i that fell in the gap range
            for x in S_i:
                dist_x = self.bd.get(x, float("inf"))
                dist_tuple = (dist_x, x)
                # Check range [B_i_prime, B_i) with tuple comparison
                if B_i_prime <= dist_tuple < B_i and x not in complete:
                    K.append((x, dist_x))
            
            if K:
                queue.batch_prepend(K)
        
        # Line 22: return B' ← min{B_i', B}; U ← U ∪ {x ∈ W : d̂[x] < B'}
        best_boundary = min(last_B_prime, upper_bound)
        
        # Include frontier vertices with distance < boundary (tuple comparison)
        final_complete = complete | {
            v for v in frontier
            if (self.bd.get(v, float("inf")), v) < best_boundary
        }
        
        return BMSSPResult(boundary=best_boundary, complete=final_complete)

    def _base_case(
        self,
        upper_bound: Tuple[float, int],
        sources: Set[int]
    ) -> BMSSPResult:
        """
        Base case: Dijkstra-style expansion for small subproblems.
        """
        # Priority queue: (distance, vertex)
        heap: List[Tuple[float, int]] = []
        for s in sources:
            d = self.bd.get(s, float("inf"))
            if (d, s) < upper_bound:
                heapq.heappush(heap, (d, s))
        
        discovered: Set[int] = set()
        
        # Safety limit for base case iterations (only in debug mode)
        if DEBUG_MODE:
            base_iterations = 0
            max_base_iterations = max(len(list(self.graph.nodes)) * 5, 1000)
        
        while heap and len(discovered) <= self.k:
            # Safety check (only in debug mode)
            if DEBUG_MODE:
                base_iterations += 1
                if base_iterations > max_base_iterations:
                    raise RuntimeError(
                        f"Base case exceeded {max_base_iterations} iterations. "
                        "Possible infinite loop detected."
                    )
            
            dist_u, u = heapq.heappop(heap)
            
            # Skip if this is a stale entry
            if dist_u > self.bd.get(u, float("inf")):
                continue
            if (dist_u, u) >= upper_bound:
                continue
            if u in discovered:
                continue
            
            discovered.add(u)
            
            # Relax outgoing edges (paper lines 7-10)
            for edge in self._adj.get(u, []):
                v = edge.target
                new_dist = dist_u + edge.weight
                
                # Paper line 7: both conditions must be met for relaxation and insertion
                # Use tuple comparison for upper bound check
                if new_dist <= self.bd.get(v, float("inf")) and (new_dist, v) < upper_bound:
                    if new_dist < self.bd.get(v, float("inf")):
                        self.bd[v] = new_dist
                        self.pred[v] = u
                    # Only push to heap when relaxation occurs (inside the if block)
                    if v not in discovered:
                        heapq.heappush(heap, (new_dist, v))
        
        # Compute boundary and complete set
        if len(discovered) <= self.k:
            # Processed everything within bound
            return BMSSPResult(boundary=upper_bound, complete=discovered)
        else:
            # Found k+1 vertices - boundary is the (k+1)th distance
            # Collect (dist, id) pairs
            vals = []
            for v in discovered:
                vals.append((self.bd[v], v))
            sorted_vals = sorted(vals)
            
            if len(sorted_vals) > self.k:
                boundary = sorted_vals[self.k] # The (k+1)-th element is the boundary
                complete = {v for v in discovered if (self.bd[v], v) < boundary}
            else:
                boundary = upper_bound
                complete = discovered
            
            return BMSSPResult(boundary=boundary, complete=complete)

    def _find_pivots(
        self,
        upper_bound: Tuple[float, int],
        sources: Set[int]
    ) -> Tuple[Set[int], Set[int]]:
        """
        Find pivot vertices and expand the frontier.
        """
        frontier: Set[int] = set(sources)
        current_layer: Set[int] = set(sources)
        
        # k rounds of expansion (Bellman-Ford style)
        for round_num in range(self.k):
            next_layer: Set[int] = set()
            
            for u in current_layer:
                dist_u = self.bd.get(u, float("inf"))
                if (dist_u, u) >= upper_bound:
                    continue
                
                for edge in self._adj.get(u, []):
                    v = edge.target
                    new_dist = dist_u + edge.weight
                    
                    # Relaxation - only add to next layer if relaxation occurs (paper line 6-9)
                    if new_dist <= self.bd.get(v, float("inf")):
                        if new_dist < self.bd.get(v, float("inf")):
                            self.bd[v] = new_dist
                            self.pred[v] = u
                        # Add to next layer only when relaxation happens and within bound
                        if (new_dist, v) < upper_bound:
                            next_layer.add(v)
            
            frontier.update(next_layer)
            current_layer = next_layer
            
            # Early termination: frontier is large relative to sources
            if len(frontier) > self.k * max(1, len(sources)):
                return set(sources), frontier
        
        # Build equality subgraph (forest)
        # Edge (u, v) exists iff bd[u] + w(u,v) = bd[v]
        equality_children: Dict[int, List[int]] = defaultdict(list)
        
        for u in frontier:
            dist_u = self.bd.get(u, float("inf"))
            if (dist_u, u) >= upper_bound:
                continue
            
            for edge in self._adj.get(u, []):
                v = edge.target
                if v not in frontier:
                    continue
                
                expected_dist = dist_u + edge.weight
                actual_dist = self.bd.get(v, float("inf"))
                
                # Check equality with numerical tolerance
                if self._is_equal(expected_dist, actual_dist):
                    equality_children[u].append(v)
        
        # Compute subtree sizes and identify pivots
        subtree_size: Dict[int, int] = {}
        pivots: Set[int] = set()
        
        for s in sources:
            if s in frontier:
                size = self._compute_subtree_size(s, equality_children, subtree_size, set())
                if size >= self.k:
                    pivots.add(s)
        
        return pivots, frontier

    def _compute_subtree_size(
        self,
        root: int,
        children: Dict[int, List[int]],
        cache: Dict[int, int],
        visited: Set[int],
        depth: int = 0
    ) -> int:
        """
        Compute size of subtree rooted at 'root' in the equality forest.
        """
        # Safety limit to prevent stack overflow (only in debug mode)
        if DEBUG_MODE:
            max_depth = min(len(list(self.graph.nodes)), 10000)
            if depth > max_depth:
                return 1  # Bail out safely
        
        if root in cache:
            return cache[root]
        
        if root in visited:
            # Cycle detected - return 0 to avoid infinite recursion
            return 0
        
        visited.add(root)
        
        size = 1  # Count self
        for child in children.get(root, []):
            size += self._compute_subtree_size(child, children, cache, visited, depth + 1)
        
        cache[root] = size
        return size

    @staticmethod
    def _is_equal(a: float, b: float, rel_tol: float = 1e-9, abs_tol: float = 1e-12) -> bool:
        """Check if two floats are approximately equal."""
        return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


