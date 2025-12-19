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
Algorithm Tracer - Captures step-by-step execution for visualization.

Records each step of Dijkstra and Sorting Barrier algorithms so they
can be played back in the visualization frontend.
"""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Set, Tuple, Any
from collections import defaultdict
import json

from graph import Graph, Edge


@dataclass
class AlgorithmStep:
    """A single step in the algorithm execution."""
    step_num: int
    action: str  # "init", "visit", "relax", "update", "finalize", "complete"
    node: Optional[int] = None
    edge: Optional[Tuple[int, int]] = None
    distance: Optional[float] = None
    message: str = ""
    
    # Current state snapshot
    distances: Dict[int, float] = field(default_factory=dict)
    visited: Set[int] = field(default_factory=set)
    frontier: Set[int] = field(default_factory=set)
    current_node: Optional[int] = None
    
    # Theoretical cost tracking (for visualization comparison)
    cost: float = 0.0  # Cumulative theoretical cost in base units
    cost_label: str = ""  # e.g., "12 log n" or "5 √log n"
    sorting_ops: int = 0  # Number of sorting-related operations (heap ops)
    total_work: float = 0.0  # Total theoretical work done
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_num": self.step_num,
            "action": self.action,
            "node": self.node,
            "edge": list(self.edge) if self.edge else None,
            "distance": self.distance if self.distance != float("inf") else None,
            "message": self.message,
            "distances": {k: (v if v != float("inf") else None) for k, v in self.distances.items()},
            "visited": list(self.visited),
            "frontier": list(self.frontier),
            "current_node": self.current_node,
            "cost": self.cost,
            "cost_label": self.cost_label,
            "sorting_ops": self.sorting_ops,
            "total_work": self.total_work,
        }


class DijkstraTracer:
    """Dijkstra's algorithm with step-by-step tracing - highlights sorting operations."""
    
    def __init__(self, graph: Graph) -> None:
        self.graph = graph
        self.steps: List[AlgorithmStep] = []
        self._step_num = 0
        
        # Count heap operations to show sorting cost
        self._heap_inserts = 0
        self._heap_extracts = 0
        self._sorting_ops = 0  # Total sorting operations (each costs O(log n))
        
        n = len(list(graph.nodes))
        self._n = n
        self._log_n = max(1, math.log2(max(2, n)))
        self._cumulative_cost = 0.0  # In units of "log n"
        self._total_work = 0.0  # Actual work: sorting_ops * log_n
    
    def _add_step(
        self,
        action: str,
        distances: Dict[int, float],
        visited: Set[int],
        frontier: Set[int],
        node: Optional[int] = None,
        edge: Optional[Tuple[int, int]] = None,
        distance: Optional[float] = None,
        message: str = "",
        current_node: Optional[int] = None,
        cost_delta: float = 0.0,
        is_sorting_op: bool = False,
    ) -> None:
        self._step_num += 1
        self._cumulative_cost += cost_delta
        if is_sorting_op:
            self._sorting_ops += 1
        self._total_work = self._sorting_ops * self._log_n
        
        step = AlgorithmStep(
            step_num=self._step_num,
            action=action,
            node=node,
            edge=edge,
            distance=distance,
            message=message,
            distances=dict(distances),
            visited=set(visited),
            frontier=set(frontier),
            current_node=current_node,
            cost=self._cumulative_cost,
            cost_label=f"Sorting: {self._sorting_ops} × log n = {self._total_work:.0f}",
            sorting_ops=self._sorting_ops,
            total_work=self._total_work,
        )
        self.steps.append(step)
    
    def run(self, source: int) -> Tuple[Dict[int, float], List[AlgorithmStep]]:
        """Run Dijkstra with tracing - shows heap/sorting operations."""
        dist: Dict[int, float] = {node: float("inf") for node in self.graph.nodes}
        pred: Dict[int, Optional[int]] = {node: None for node in self.graph.nodes}
        visited: Set[int] = set()
        n = len(dist)
        
        dist[source] = 0.0
        heap: List[Tuple[float, int]] = [(0.0, source)]
        frontier = {source}
        
        # Count initial insert - costs 1 * log(n)
        self._heap_inserts = 1
        
        self._add_step(
            action="init",
            distances=dist,
            visited=visited,
            frontier=frontier,
            node=source,
            distance=0.0,
            message=f"Initialize. Each heap op costs O(log n) ≈ {self._log_n:.1f}",
            cost_delta=1.0,
            is_sorting_op=True,
        )
        
        while heap:
            # Extract-min is O(log n) - the sorting bottleneck!
            d, u = heapq.heappop(heap)
            self._heap_extracts += 1
            
            if u in visited:
                continue
            
            frontier.discard(u)
            
            self._add_step(
                action="visit",
                distances=dist,
                visited=visited,
                frontier=frontier,
                node=u,
                distance=d,
                message=f"⚠️ HEAP EXTRACT-MIN: O(log n) sorting cost!",
                current_node=u,
                cost_delta=1.0,
                is_sorting_op=True,
            )
            
            visited.add(u)
            
            for edge in self.graph.neighbors(u):
                v = edge.target
                new_dist = d + edge.weight
                
                if new_dist < dist[v]:
                    old_dist = dist[v]
                    dist[v] = new_dist
                    pred[v] = u
                    
                    if v not in visited:
                        frontier.add(v)
                        heapq.heappush(heap, (new_dist, v))
                        self._heap_inserts += 1
                    
                        self._add_step(
                            action="relax",
                            distances=dist,
                            visited=visited,
                            frontier=frontier,
                            node=v,
                            edge=(u, v),
                            distance=new_dist,
                            message=f"⚠️ HEAP INSERT ({u}→{v}): O(log n) sorting cost!",
                            current_node=u,
                            cost_delta=1.0,
                            is_sorting_op=True,
                        )
            
            self._add_step(
                action="finalize",
                distances=dist,
                visited=visited,
                frontier=frontier,
                node=u,
                distance=dist[u],
                message=f"Finalized node {u}",
                current_node=None,
                cost_delta=0.0,
            )
        
        self._add_step(
            action="complete",
            distances=dist,
            visited=visited,
            frontier=set(),
            message=f"Done! Total: {self._sorting_ops} heap ops × O(log n) = O({self._sorting_ops} log n)",
            cost_delta=0.0,
        )
        
        return dist, self.steps


class SortingBarrierTracer:
    """Sorting Barrier SSSP with step-by-step tracing using the real algorithm.
    
    This tracer faithfully implements the algorithms from the paper:
    - Algorithm 1: FindPivots(B, S)
    - Algorithm 2: BaseCase(B, S)  
    - Algorithm 3: BMSSP(l, B, S)
    
    Uses the PartialSort data structure (Lemma 3.3) for sub-logarithmic sorting.
    Key insight: Each sorting operation costs O(√log n) instead of O(log n)!
    """
    
    def __init__(self, graph: Graph) -> None:
        from algorithms.sorting_barrier_sssp import SortingBarrierSSSP
        from datastructures.partial_sort import PartialSort
        
        self.graph = graph
        self.steps: List[AlgorithmStep] = []
        self._step_num = 0
        
        # Create the real algorithm instance for parameters
        self._algo = SortingBarrierSSSP(graph)
        self.k = self._algo.k
        self.t = self._algo.t
        self.max_level = self._algo.max_level
        
        # Track state for visualization
        self._visited: Set[int] = set()
        self._frontier: Set[int] = set()
        self._current_node: Optional[int] = None
        
        # Track theoretical cost
        n = len(list(graph.nodes))
        self._n = n
        self._sqrt_log_n = max(1, math.sqrt(math.log2(max(2, n))))
        self._log_n = max(1, math.log2(max(2, n)))
        self._cumulative_cost = 0.0  # In units of √log n
        self._sorting_ops = 0  # Number of "sorting" operations (each costs O(√log n))
        self._total_work = 0.0  # Total work: sorting_ops * sqrt_log_n
        self._relaxations = 0
        
        # Store PartialSort class for creating instances
        self._PartialSort = PartialSort
    
    def _add_step(
        self,
        action: str,
        node: Optional[int] = None,
        edge: Optional[Tuple[int, int]] = None,
        distance: Optional[float] = None,
        message: str = "",
        current_node: Optional[int] = None,
        cost_delta: float = 0.0,
        is_sorting_op: bool = False,
    ) -> None:
        self._step_num += 1
        self._cumulative_cost += cost_delta
        if is_sorting_op:
            self._sorting_ops += 1
        self._total_work = self._sorting_ops * self._sqrt_log_n
        
        step = AlgorithmStep(
            step_num=self._step_num,
            action=action,
            node=node,
            edge=edge,
            distance=distance,
            message=message,
            distances=dict(self._algo.bd),
            visited=set(self._visited),
            frontier=set(self._frontier),
            current_node=current_node or self._current_node,
            cost=self._cumulative_cost,
            cost_label=f"Sorting: {self._sorting_ops} × √log n = {self._total_work:.1f}",
            sorting_ops=self._sorting_ops,
            total_work=self._total_work,
        )
        self.steps.append(step)
    
    def run(self, source: int) -> Tuple[Dict[int, float], List[AlgorithmStep]]:
        """Run Sorting Barrier with tracing by instrumenting the real algorithm.
        
        Implements the full algorithm from the paper with step-by-step tracing:
        - Algorithm 1: FindPivots (k rounds of BF relaxation + equality forest)
        - Algorithm 2: BaseCase (bounded Dijkstra for ≤k vertices)
        - Algorithm 3: BMSSP (recursive with PartialSort blocks)
        """
        
        # Initialize distances
        for node in self.graph.nodes:
            self._algo.bd[node] = float("inf")
            self._algo.pred[node] = None
        
        self._algo.bd[source] = 0.0
        self._frontier = {source}
        
        n = self._n
        self._add_step(
            action="init",
            node=source,
            distance=0.0,
            message=f"Init: n={n}. Each sort op costs O(√log n) ≈ {self._sqrt_log_n:.2f} (not log n ≈ {self._log_n:.1f}!)",
            cost_delta=0.0,
        )
        
        # Run the algorithm with tracing
        self._traced_bmssp(
            level=self._algo.max_level,
            upper_bound=(float("inf"), 0),
            sources={source},
            depth=0
        )
        
        self._add_step(
            action="complete",
            message=f"Done! {self._sorting_ops} sort ops × O(√log n) = O({self._sorting_ops} √log n)",
            cost_delta=0.0,
        )
        
        return dict(self._algo.bd), self.steps
    
    def _traced_bmssp(
        self,
        level: int,
        upper_bound: Tuple[float, int],
        sources: Set[int],
        depth: int
    ) -> Tuple[Tuple[float, int], Set[int]]:
        """BMSSP with tracing - Algorithm 3 from paper.
        
        Uses PartialSort (Lemma 3.3) for sub-logarithmic block extraction.
        """
        
        if not sources:
            return upper_bound, set()
        
        indent = "  " * depth
        ub_val = upper_bound[0]
        
        # Line 2-3: Base case (l = 0)
        if level == 0:
            self._add_step(
                action="visit",
                message=f"{indent}BaseCase (l=0): Dijkstra for ≤k vertices",
                cost_delta=0.1,
            )
            return self._traced_base_case(upper_bound, sources, depth)
        
        # Line 4: P, W ← FindPivots(B, S)
        self._add_step(
            action="visit",
            message=f"{indent}Level {level}: FindPivots(B={ub_val:.1f}, |S|={len(sources)})",
        )
        
        pivots, frontier = self._traced_find_pivots(upper_bound, sources, depth)
        self._frontier.update(frontier)
        
        # Line 5: D.Initialize(M, B) with M = 2^{(l-1)t}
        block_size = 2 ** ((level - 1) * self.t)
        block_size = max(1, min(block_size, len(list(self.graph.nodes))))
        
        # Use PartialSort - the key data structure from Lemma 3.3
        D = self._PartialSort(upper_bound=ub_val, block_size=block_size)
        
        self._add_step(
            action="visit",
            message=f"{indent}D.Initialize(M={block_size}, B={ub_val:.1f}) ✓ O(1)",
        )
        
        # Line 6: D.Insert(⟨x, d̂[x]⟩) for x ∈ P
        for p in pivots:
            if (self._algo.bd[p], p) < upper_bound:
                D.insert(p, self._algo.bd[p])
        
        if pivots:
            self._add_step(
                action="visit",
                message=f"{indent}Inserted {len(pivots)} pivots into D ✓ O(|P|)",
            )
        
        # Line 7: i ← 0; B_0' ← min_{x∈P} d̂[x]; U ← ∅
        if pivots:
            pivot_dists = [(self._algo.bd[p], p) for p in pivots if self._algo.bd[p] < float("inf")]
            B_prev = min(pivot_dists) if pivot_dists else upper_bound
        else:
            B_prev = upper_bound
        
        complete: Set[int] = set()  # U in paper
        
        # Line 8 condition: |U| < k·2^{lt}
        max_complete = self.k * (2 ** (level * self.t))
        
        iteration = 0
        last_B_prime = B_prev
        
        # Line 8: while |U| < k·2^{lt} and D is non-empty
        while len(complete) < max_complete and not D.is_empty():
            iteration += 1
            
            # Line 10: B_i, S_i ← D.Pull()
            B_i, S_i = D.pull()
            
            if not S_i:
                break
            
            # Filter out already completed vertices
            S_i = {v for v in S_i if v not in complete}
            if not S_i:
                continue
            
            # B_i is a tuple (priority, key)
            bi_val = B_i[0]
            
            self._add_step(
                action="visit",
                message=f"{indent}✓ D.Pull(): O(√log n) partial sort (not O(log n)!)",
                cost_delta=1.0,
                is_sorting_op=True,  # Key: costs O(√log n), not O(log n)!
            )
            
            # Line 11: B_i', U_i ← BMSSP(l-1, B_i, S_i)
            B_i_prime, U_i = self._traced_bmssp(level - 1, B_i, S_i, depth + 1)
            
            # Line 12: U ← U ∪ U_i
            complete.update(U_i)
            self._visited.update(U_i)
            self._frontier -= U_i
            
            last_B_prime = B_i_prime
            
            # Line 13: K ← ∅
            K: List[Tuple[int, float]] = []
            
            # Lines 14-20: Process edges from U_i
            for u in U_i:
                dist_u = self._algo.bd[u]
                self._current_node = u
                
                for edge in self._algo._adj.get(u, []):
                    v = edge.target
                    new_dist = dist_u + edge.weight
                    
                    # Line 15: if d̂[u] + w_uv ≤ d̂[v]
                    if new_dist <= self._algo.bd.get(v, float("inf")):
                        # Line 16: d̂[v] ← d̂[u] + w_uv
                        if new_dist < self._algo.bd.get(v, float("inf")):
                            self._algo.bd[v] = new_dist
                            self._algo.pred[v] = u
                            self._relaxations += 1
                            
                            self._add_step(
                                action="relax",
                                node=v,
                                edge=(u, v),
                                distance=new_dist,
                                message=f"{indent}  Relax ({u}→{v}): d̂[{v}]={new_dist:.2f} ✓ O(1)",
                                current_node=u,
                                cost_delta=0.01,
                            )
                        
                        # Skip if already completed
                        if v in complete:
                            continue
                        
                        dist_tuple = (new_dist, v)
                        
                        # Line 17-18: if d̂[u] + w_uv ∈ [B_i, B) then D.Insert
                        if B_i <= dist_tuple < upper_bound:
                            D.insert(v, new_dist)
                            self._frontier.add(v)
                        # Line 19-20: else if d̂[u] + w_uv ∈ [B_i', B_i) then K ← K ∪ {v}
                        elif B_i_prime <= dist_tuple < B_i:
                            K.append((v, new_dist))
                            self._frontier.add(v)
            
            # Line 21: D.BatchPrepend(K ∪ {x ∈ S_i : d̂[x] ∈ [B_i', B_i)})
            for x in S_i:
                dist_x = self._algo.bd.get(x, float("inf"))
                dist_tuple = (dist_x, x)
                if B_i_prime <= dist_tuple < B_i and x not in complete:
                    K.append((x, dist_x))
            
            if K:
                D.batch_prepend(K)
                bi_prime_val = B_i_prime[0]
                self._add_step(
                    action="visit",
                    message=f"{indent}D.BatchPrepend({len(K)} items in [B'={bi_prime_val:.2f}, B_i={bi_val:.2f})) ✓ O(|K|)",
                    cost_delta=0.1,
                )
        
        # Line 22: return B' ← min{B_i', B}; U ← U ∪ {x ∈ W : d̂[x] < B'}
        best_boundary = min(last_B_prime, upper_bound)
        final_complete = complete | {
            v for v in frontier
            if (self._algo.bd.get(v, float("inf")), v) < best_boundary
        }
        
        return best_boundary, final_complete
    
    def _traced_base_case(
        self,
        upper_bound: Tuple[float, int],
        sources: Set[int],
        depth: int
    ) -> Tuple[Tuple[float, int], Set[int]]:
        """Base case with tracing - Algorithm 2 from paper.
        
        Dijkstra-style expansion stopping at k+1 vertices.
        Note: Paper assumes |S|=1, but we handle multi-source for generality.
        """
        indent = "  " * depth
        
        # Line 2: U_0 ← S (initialize with sources)
        # Line 3: Initialize heap H with sources
        heap: List[Tuple[float, int]] = []
        for s in sources:
            d = self._algo.bd.get(s, float("inf"))
            if (d, s) < upper_bound:
                heapq.heappush(heap, (d, s))
        
        # U_0 tracks discovered vertices
        U_0: Set[int] = set()
        
        # Track vertices in heap for DecreaseKey simulation
        in_heap: Set[int] = set(sources)
        
        # Line 4: while H is non-empty and |U_0| < k + 1
        while heap and len(U_0) < self.k + 1:
            # Line 5: ⟨u, d̂[u]⟩ ← H.ExtractMin()
            dist_u, u = heapq.heappop(heap)
            
            # Skip stale entries (simulates DecreaseKey behavior)
            if dist_u > self._algo.bd.get(u, float("inf")):
                continue
            if (dist_u, u) >= upper_bound:
                continue
            if u in U_0:
                continue
            
            # Line 6: U_0 ← U_0 ∪ {u}
            U_0.add(u)
            self._visited.add(u)
            self._frontier.discard(u)
            
            self._add_step(
                action="finalize",
                node=u,
                distance=dist_u,
                message=f"{indent}U_0 ← U_0 ∪ {{{u}}} (|U_0|={len(U_0)}/{self.k+1}) ✓ O(log k)",
                current_node=u,
                cost_delta=0.05,  # O(log k) for heap op, but k is small
            )
            
            # Lines 7-13: for edge e = (u, v)
            for edge in self._algo._adj.get(u, []):
                v = edge.target
                new_dist = dist_u + edge.weight
                
                # Line 8: if d̂[u] + w_uv ≤ d̂[v] and d̂[u] + w_uv < B
                if new_dist <= self._algo.bd.get(v, float("inf")) and (new_dist, v) < upper_bound:
                    # Line 9: d̂[v] ← d̂[u] + w_uv
                    if new_dist < self._algo.bd.get(v, float("inf")):
                        self._algo.bd[v] = new_dist
                        self._algo.pred[v] = u
                        self._relaxations += 1
                        
                        self._add_step(
                            action="relax",
                            node=v,
                            edge=(u, v),
                            distance=new_dist,
                            message=f"{indent}  d̂[{v}] ← {new_dist:.2f} ✓ O(1)",
                            current_node=u,
                            cost_delta=0.01,
                        )
                    
                    # Lines 10-13: Insert or DecreaseKey
                    if v not in U_0:
                        self._frontier.add(v)
                        heapq.heappush(heap, (new_dist, v))
                        in_heap.add(v)
        
        # Lines 14-17: Compute boundary and return
        if len(U_0) <= self.k:
            # Line 15: return B' ← B, U ← U_0
            self._add_step(
                action="visit",
                message=f"{indent}BaseCase done: |U_0|={len(U_0)} ≤ k={self.k}, B'=B",
            )
            return upper_bound, U_0
        else:
            # Line 17: B' ← max_{v∈U_0} d̂[v], U ← {v ∈ U_0 : d̂[v] < B'}
            sorted_items = sorted([(self._algo.bd[v], v) for v in U_0])
            # B' is the k-th smallest (0-indexed: index k is the (k+1)-th element)
            boundary = sorted_items[self.k] if len(sorted_items) > self.k else upper_bound
            # Return first k vertices (those with distance < boundary)
            # In case of ties at the boundary, we still return k vertices
            complete = {v for d, v in sorted_items[:self.k]}
            
            boundary_val = boundary[0]
            
            self._add_step(
                action="visit",
                message=f"{indent}BaseCase done: |U_0|={len(U_0)} > k, B'={boundary_val:.2f}, |U|={len(complete)}",
            )
            return boundary, complete
    
    def _traced_find_pivots(
        self,
        upper_bound: Tuple[float, int],
        sources: Set[int],
        depth: int
    ) -> Tuple[Set[int], Set[int]]:
        """Find pivots with tracing - Algorithm 1 from paper.
        
        Performs k rounds of Bellman-Ford relaxation, then identifies pivots
        as sources with subtree size ≥ k in the equality forest.
        """
        indent = "  " * depth
        
        # Line 2: W ← S
        # Line 3: W_0 ← S
        W: Set[int] = set(sources)  # Frontier (accumulated)
        W_prev: Set[int] = set(sources)  # W_{i-1} for iteration
        
        # Line 4: for i ← 1 to k do (k rounds of relaxation)
        for i in range(1, self.k + 1):
            # Line 5: W_i ← ∅
            W_i: Set[int] = set()
            
            self._add_step(
                action="visit",
                message=f"{indent}FindPivots round {i}/{self.k}: relaxing from |W_{i-1}|={len(W_prev)} vertices",
                cost_delta=0.1,
            )
            
            # Line 6: for all edges (u, v) with u ∈ W_{i-1}
            for u in W_prev:
                dist_u = self._algo.bd.get(u, float("inf"))
                if (dist_u, u) >= upper_bound:
                    continue
                
                for edge in self._algo._adj.get(u, []):
                    v = edge.target
                    new_dist = dist_u + edge.weight
                    
                    # Line 7: if d̂[u] + w_uv ≤ d̂[v]
                    if new_dist <= self._algo.bd.get(v, float("inf")):
                        # Line 8: d̂[v] ← d̂[u] + w_uv
                        if new_dist < self._algo.bd.get(v, float("inf")):
                            self._algo.bd[v] = new_dist
                            self._algo.pred[v] = u
                            self._relaxations += 1
                            
                            self._add_step(
                                action="relax",
                                node=v,
                                edge=(u, v),
                                distance=new_dist,
                                message=f"{indent}  d̂[{v}] ← d̂[{u}] + w = {new_dist:.2f} ✓ O(1)",
                                current_node=u,
                                cost_delta=0.01,
                            )
                        
                        # Line 9-10: if d̂[u] + w_uv < B then W_i ← W_i ∪ {v}
                        if (new_dist, v) < upper_bound:
                            W_i.add(v)
            
            # Line 11: W ← W ∪ W_i
            W.update(W_i)
            
            # Line 12-14: if |W| > k|S| then return P ← S, W
            if len(W) > self.k * max(1, len(sources)):
                self._add_step(
                    action="visit",
                    message=f"{indent}Early exit: |W|={len(W)} > k·|S|={self.k * len(sources)} → P=S",
                )
                return set(sources), W
            
            W_prev = W_i
        
        # Line 15: F ← {(u,v) ∈ E : u,v ∈ W, d̂[v] = d̂[u] + w_uv}
        # Build equality forest F
        equality_children: Dict[int, List[int]] = defaultdict(list)
        
        for u in W:
            dist_u = self._algo.bd.get(u, float("inf"))
            if (dist_u, u) >= upper_bound:
                continue
            
            for edge in self._algo._adj.get(u, []):
                v = edge.target
                if v not in W:
                    continue
                
                expected_dist = dist_u + edge.weight
                actual_dist = self._algo.bd.get(v, float("inf"))
                
                # Check equality: d̂[v] = d̂[u] + w_uv
                if abs(expected_dist - actual_dist) < 1e-9:
                    equality_children[u].append(v)
        
        # Line 16: P ← {u ∈ S : u is root of tree with ≥ k vertices in F}
        subtree_size: Dict[int, int] = {}
        pivots: Set[int] = set()
        
        for s in sources:
            if s in W:
                size = self._compute_subtree_size(s, equality_children, subtree_size, set())
                if size >= self.k:
                    pivots.add(s)
        
        self._add_step(
            action="visit",
            message=f"{indent}FindPivots done: |W|={len(W)}, |P|={len(pivots)} pivots with subtree ≥ k={self.k}",
        )
        
        # Line 17: return P, W
        return pivots, W
    
    def _compute_subtree_size(
        self,
        root: int,
        children: Dict[int, List[int]],
        cache: Dict[int, int],
        visited: Set[int]
    ) -> int:
        """Compute subtree size in equality forest."""
        if root in cache:
            return cache[root]
        if root in visited:
            return 0
        
        visited.add(root)
        size = 1
        for child in children.get(root, []):
            size += self._compute_subtree_size(child, children, cache, visited)
        
        cache[root] = size
        return size


def generate_visualization_data(graph: Graph, source: int) -> Dict[str, Any]:
    """Generate complete visualization data for both algorithms."""
    
    # Get graph structure
    nodes = list(graph.nodes)
    edges = []
    for u in nodes:
        for edge in graph.neighbors(u):
            edges.append({
                "source": u,
                "target": edge.target,
                "weight": round(edge.weight, 2)
            })
    
    # Run both algorithms with tracing
    dijkstra_tracer = DijkstraTracer(graph)
    dijkstra_dist, dijkstra_steps = dijkstra_tracer.run(source)
    
    sb_tracer = SortingBarrierTracer(graph)
    sb_dist, sb_steps = sb_tracer.run(source)
    
    return {
        "graph": {
            "nodes": nodes,
            "edges": edges,
            "source": source,
        },
        "dijkstra": {
            "name": "Dijkstra's Algorithm",
            "steps": [s.to_dict() for s in dijkstra_steps],
            "final_distances": {k: (v if v != float("inf") else None) for k, v in dijkstra_dist.items()},
        },
        "sorting_barrier": {
            "name": "Sorting Barrier SSSP",
            "steps": [s.to_dict() for s in sb_steps],
            "final_distances": {k: (v if v != float("inf") else None) for k, v in sb_dist.items()},
        },
    }

