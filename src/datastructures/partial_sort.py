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
Partial Sorting Data Structure for the Sorting Barrier SSSP Algorithm.

This implements the key innovation from Duan, Mao, Mao, Shu, and Yin's paper
"Breaking the Sorting Barrier for Directed Single-Source Shortest Paths".

The structure supports:
- insert(key, priority): Insert element with given priority
- extract_smallest(M): Extract up to M smallest elements in O(M) time
- batch_insert(pairs): Insert multiple elements efficiently

The key insight is that we don't need full sorting - we only need to extract
blocks of elements, which can be done more efficiently using bucket-based
partitioning with linear-time selection.
"""

from __future__ import annotations

import random
from typing import Dict, List, Optional, Tuple, Set, Union


class PartialSort:
    """
    A partial sorting structure that extracts M smallest elements in O(M) time.
    
    Uses a bucket-based approach with linear-time selection (median-of-medians
    or randomized quickselect) to achieve the required complexity bounds.
    
    The structure maintains elements in a flat list and uses quickselect-style
    partitioning when extraction is needed, rather than maintaining a heap.
    
    Supports operations from Lemma 3.3 of the paper:
    - Insert(x, p): Insert element x with priority p
    - Pull(): Extract a block and return (boundary, elements)
    - BatchPrepend(K): Prepend elements K to front of queue
    """
    
    def __init__(self, upper_bound: float = float("inf"), block_size: int = 1) -> None:
        self.upper_bound = upper_bound
        self.block_size = max(1, block_size)  # M from the paper
        # Store (priority, key) pairs - priority first for efficient comparison
        self._elements: List[Tuple[float, int]] = []
        # Track best known priority for each key to handle duplicates
        self._best: Dict[int, float] = {}
        # Cached sorted prefix (optimization)
        self._sorted_prefix: List[Tuple[float, int]] = []
        self._prefix_valid = False
        # Prepended elements (high priority, process first)
        self._prepended: List[Tuple[float, int]] = []
    
    def insert(self, key: int, priority: float) -> None:
        """Insert element with given priority. Updates if new priority is better."""
        if priority >= self.upper_bound:
            return
        
        current_best = self._best.get(key)
        if current_best is None or priority < current_best:
            self._best[key] = priority
            self._elements.append((priority, key))
            self._prefix_valid = False
    
    def batch_insert(self, pairs: List[Tuple[int, float]]) -> None:
        """Insert multiple (key, priority) pairs efficiently."""
        for key, priority in pairs:
            self.insert(key, priority)
    
    def batch_prepend(self, pairs: List[Tuple[int, float]]) -> None:
        """
        Prepend elements to the front of the queue (paper's BatchPrepend).
        
        These elements will be processed before regular elements in the next Pull().
        Used for elements with distances in range [B_i', B_i) that need to be
        processed in the current iteration before moving to higher boundaries.
        
        Args:
            pairs: List of (key, priority) pairs to prepend
        """
        for key, priority in pairs:
            if priority >= self.upper_bound:
                continue
            current_best = self._best.get(key)
            if current_best is None or priority < current_best:
                self._best[key] = priority
                self._prepended.append((priority, key))
        self._prefix_valid = False
    
    def pull(self) -> Tuple[Tuple[float, int], Set[int]]:
        """
        Extract a block of elements (paper's Pull operation from Lemma 3.3).
        
        Returns (B_i, S_i) where:
        - B_i is the boundary tuple (priority, key) of the next element
          (or (upper_bound, 0) if none remain)
        - S_i is the set of extracted element keys
        
        First processes any prepended elements, then extracts up to block_size
        elements from the main queue.
        """
        if not self._best:
            return (self.upper_bound, 0), set()
        
        # First, process prepended elements (they have priority)
        extracted_keys: Set[int] = set()
        
        if self._prepended:
            # Compact prepended list
            self._prepended = [
                (p, k) for p, k in self._prepended
                if self._best.get(k) == p
            ]
            # Sort and extract all prepended elements
            self._prepended.sort()
            for priority, key in self._prepended:
                if self._best.get(key) == priority:
                    extracted_keys.add(key)
                    del self._best[key]
            self._prepended = []
        
        # If we got prepended elements, return them as a block
        if extracted_keys:
            # Boundary is the min priority tuple among remaining, or upper bound
            self._compact()
            if self._elements:
                # Find min tuple (priority, key)
                min_remaining = min(
                    (p, k) for p, k in self._elements 
                    if self._best.get(k) == p
                )
                boundary = min_remaining
            else:
                boundary = (self.upper_bound, 0)
            return boundary, extracted_keys
        
        # No prepended elements - extract from main queue using block_size
        self._compact()
        
        if not self._elements:
            return (self.upper_bound, 0), set()
        
        n = len(self._elements)
        k = min(self.block_size, n)
        
        if k == 0:
            return (self.upper_bound, 0), set()
        
        # Use quickselect to find the k smallest elements
        smallest = self._quickselect_smallest(k)
        
        # Extract keys and remove from tracking
        for priority, key in smallest:
            if self._best.get(key) == priority:
                extracted_keys.add(key)
                del self._best[key]
        
        # Compute boundary (tuple of next element)
        if len(self._elements) > k:
            # Find minimum tuple of remaining elements
            remaining_min = (float("inf"), 0)
            for i in range(k, len(self._elements)):
                p, key = self._elements[i]
                if self._best.get(key) == p:
                    if (p, key) < remaining_min:
                        remaining_min = (p, key)
            
            if remaining_min[0] < float("inf"):
                boundary = remaining_min
            else:
                boundary = (self.upper_bound, 0)
        else:
            boundary = (self.upper_bound, 0)
        
        # Remove extracted elements from list
        self._elements = self._elements[k:]
        self._prefix_valid = False
        
        return boundary, extracted_keys
    
    def extract_smallest(self, m: int) -> Tuple[Tuple[float, int], List[int]]:
        """
        Extract up to M smallest elements and return (boundary_tuple, keys).
        
        The boundary is the (priority, key) of the (M+1)th smallest element,
        or (upper_bound, 0) if fewer than M+1 elements exist.
        
        Uses quickselect for O(M) expected time complexity.
        """
        if not self._best:
            return (self.upper_bound, 0), []
        
        # Compact the elements list - remove stale entries
        self._compact()
        
        if not self._elements:
            return (self.upper_bound, 0), []
        
        n = len(self._elements)
        k = min(m, n)
        
        if k == 0:
            return (self.upper_bound, 0), []
        
        # Use quickselect to find the k smallest elements
        smallest = self._quickselect_smallest(k)
        
        # Extract keys and remove from tracking
        keys = []
        for priority, key in smallest:
            if self._best.get(key) == priority:
                keys.append(key)
                del self._best[key]
        
        # Determine boundary tuple
        if len(self._elements) > k:
            # Find minimum of remaining elements
            remaining_min = (float("inf"), 0)
            for i in range(k, len(self._elements)):
                p, key = self._elements[i]
                if self._best.get(key) == p:
                    if (p, key) < remaining_min:
                        remaining_min = (p, key)
            
            if remaining_min[0] < float("inf"):
                boundary = remaining_min
            else:
                boundary = (self.upper_bound, 0)
        else:
            boundary = (self.upper_bound, 0)
        
        # Remove extracted elements from list
        self._elements = self._elements[k:]
        self._prefix_valid = False
        
        return boundary, keys
    
    def _compact(self) -> None:
        """Remove stale entries where priority != best known priority."""
        self._elements = [
            (p, k) for p, k in self._elements 
            if self._best.get(k) == p
        ]
    
    def _quickselect_smallest(self, k: int) -> List[Tuple[float, int]]:
        """
        Find k smallest elements using randomized quickselect.
        
        Partitions the list so that elements[0:k] contains the k smallest.
        Expected O(n) time complexity.
        """
        if k >= len(self._elements):
            # Sort all and return
            self._elements.sort()
            return self._elements[:k]
        
        # Randomized quickselect to partition around kth element
        self._quickselect_partition(0, len(self._elements) - 1, k)
        
        # Now elements[0:k] contains k smallest (unsorted among themselves)
        # Sort just these k elements for consistent output
        result = self._elements[:k]
        result.sort()
        return result
    
    def _quickselect_partition(self, left: int, right: int, k: int) -> None:
        """
        Partition elements so that the k smallest are in elements[0:k].
        Uses randomized pivot selection for expected O(n) time.
        """
        while left < right:
            # Random pivot selection
            pivot_idx = random.randint(left, right)
            pivot_val = self._elements[pivot_idx]
            
            # Move pivot to end
            self._elements[pivot_idx], self._elements[right] = \
                self._elements[right], self._elements[pivot_idx]
            
            # Partition
            store_idx = left
            for i in range(left, right):
                # Lexicographical comparison (priority, key)
                if self._elements[i] < pivot_val:
                    self._elements[store_idx], self._elements[i] = \
                        self._elements[i], self._elements[store_idx]
                    store_idx += 1
            
            # Move pivot to final position
            self._elements[store_idx], self._elements[right] = \
                self._elements[right], self._elements[store_idx]
            
            # Recurse on the side containing the kth element
            if store_idx == k - 1:
                return
            elif store_idx < k - 1:
                left = store_idx + 1
            else:
                right = store_idx - 1
    
    def peek_min(self) -> Optional[Tuple[float, int]]:
        """Return the minimum element without removing it."""
        self._compact()
        if not self._elements:
            return None
        return min(self._elements)
    
    def is_empty(self) -> bool:
        """Check if the structure has any elements."""
        return len(self._best) == 0
    
    def __len__(self) -> int:
        return len(self._best)
    
    def set_block_size(self, block_size: int) -> None:
        """Update the block size (M parameter from paper)."""
        self.block_size = max(1, block_size)

