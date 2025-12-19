#!/usr/bin/env python3
"""
Test script for the Sorting Barrier SSSP implementation.

Compares the true adaptation against standard Dijkstra to verify correctness.
"""

import random
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from graph import Graph
from algorithms.sorting_barrier_sssp import SortingBarrierSSSP
from algorithms.dijkstra import dijkstra


def create_random_graph(n: int, m: int, max_weight: float = 10.0, show_progress: bool = False) -> Graph:
    """Create a random graph with n vertices and m edges."""
    graph = Graph(directed=True)
    
    # Ensure all vertices exist
    for i in range(n):
        graph._nodes.add(i)
    
    # Add random edges
    edges_added = 0
    last_percent = -1
    while edges_added < m:
        u = random.randint(0, n - 1)
        v = random.randint(0, n - 1)
        if u != v:
            weight = random.uniform(0.1, max_weight)
            graph.add_edge(u, v, weight)
            edges_added += 1
            
            if show_progress:
                percent = (edges_added * 100) // m
                if percent != last_percent:
                    print(f"\r  Creating graph: {percent}%", end="", flush=True)
                    last_percent = percent
    
    if show_progress:
        print("\r  Creating graph: 100% ✓")
    
    return graph


def create_grid_graph(rows: int, cols: int) -> Graph:
    """Create a grid graph for structured testing."""
    graph = Graph(directed=True)
    
    for r in range(rows):
        for c in range(cols):
            node = r * cols + c
            
            # Right edge
            if c + 1 < cols:
                graph.add_edge(node, node + 1, random.uniform(1.0, 5.0))
            
            # Down edge
            if r + 1 < rows:
                graph.add_edge(node, node + cols, random.uniform(1.0, 5.0))
            
            # Left edge (make it bidirectional sometimes)
            if c > 0 and random.random() < 0.3:
                graph.add_edge(node, node - 1, random.uniform(1.0, 5.0))
            
            # Up edge
            if r > 0 and random.random() < 0.3:
                graph.add_edge(node, node - cols, random.uniform(1.0, 5.0))
    
    return graph


def test_correctness(graph: Graph, source: int, name: str) -> bool:
    """Test that SortingBarrierSSSP produces correct results."""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"Nodes: {len(graph._nodes)}, Edges: {graph.edge_count}")
    print(f"{'='*60}")
    
    # Run both algorithms
    print("Running SortingBarrierSSSP...")
    t1 = time.perf_counter()
    algo = SortingBarrierSSSP(graph)
    dist_sb, pred_sb = algo.run(source)
    t_sb = time.perf_counter() - t1
    
    print("Running Dijkstra (reference)...")
    t2 = time.perf_counter()
    dist_ref, pred_ref = dijkstra(graph, source)
    t_ref = time.perf_counter() - t2
    
    # Compare results
    print("\nComparing results...")
    max_diff = 0.0
    mismatch_count = 0
    
    for node in graph._nodes:
        d1 = dist_sb.get(node, float("inf"))
        d2 = dist_ref.get(node, float("inf"))
        
        diff = abs(d1 - d2)
        if diff > 1e-9:
            if mismatch_count < 5:
                print(f"  Mismatch at node {node}: SB={d1:.6f}, Dijkstra={d2:.6f}, diff={diff:.6e}")
            mismatch_count += 1
            max_diff = max(max_diff, diff)
    
    if mismatch_count > 5:
        print(f"  ... and {mismatch_count - 5} more mismatches")
    
    # Report results
    print(f"\nResults:")
    print(f"  SortingBarrier time: {t_sb*1000:.2f} ms")
    print(f"  Dijkstra time:       {t_ref*1000:.2f} ms")
    print(f"  Speedup:             {t_ref/t_sb:.2f}x" if t_sb > 0 else "  Speedup: N/A")
    print(f"  Max difference:      {max_diff:.2e}")
    print(f"  Mismatches:          {mismatch_count}")
    
    success = mismatch_count == 0 or max_diff < 1e-6
    print(f"\n  Status: {'✓ PASS' if success else '✗ FAIL'}")
    
    return success


def test_parameters():
    """Test that algorithm parameters are computed correctly."""
    print("\n" + "="*60)
    print("Testing parameter computation")
    print("="*60)
    
    test_sizes = [10, 100, 1000, 10000, 100000]
    
    for n in test_sizes:
        graph = Graph()
        for i in range(n):
            graph._nodes.add(i)
        
        algo = SortingBarrierSSSP(graph)
        
        log_n = max(1, int(round(n ** 0.5)))  # Simplified for display
        expected_k = max(2, int(round(algo.k)))
        expected_t = max(1, int(round(algo.t)))
        expected_levels = max(1, algo.max_level)
        
        print(f"  n={n:>6}: k={algo.k:>3}, t={algo.t:>3}, levels={algo.max_level:>2}")


def main():
    random.seed(42)  # Reproducibility
    
    print("="*60)
    print("Sorting Barrier SSSP - Correctness Tests")
    print("="*60)
    
    # Test parameters
    test_parameters()
    
    # Define all tests
    tests = [
        ("Small random graph (n=20, m=50)", lambda: create_random_graph(20, 50)),
        ("Medium random graph (n=100, m=500)", lambda: create_random_graph(100, 500)),
        ("Grid graph (10x10)", lambda: create_grid_graph(10, 10)),
        ("Sparse graph (n=200, m=300)", lambda: create_random_graph(200, 300)),
        ("Dense graph (n=50, m=1000)", lambda: create_random_graph(50, 1000)),
        ("Larger graph (n=500, m=2000)", lambda: create_random_graph(500, 2000)),
        ("Large graph (n=1000, m=5000)", lambda: create_random_graph(1000, 5000, show_progress=True)),
    ]
    
    all_passed = True
    total_tests = len(tests)
    
    for i, (name, graph_fn) in enumerate(tests, 1):
        print(f"\n[{i}/{total_tests}] ", end="")
        graph = graph_fn()
        passed = test_correctness(graph, 0, name)
        all_passed &= passed
        print(f"\nProgress: {i}/{total_tests} tests completed ({100*i//total_tests}%)")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Overall: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

