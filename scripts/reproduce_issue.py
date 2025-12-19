
import sys
import random
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from graph import Graph
from algorithms.dijkstra import dijkstra
from algorithms.sorting_barrier_sssp import SortingBarrierSSSP, BMSSPResult
from visualization.tracer import SortingBarrierTracer

def create_maze(rows: int, cols: int):
    # Copy from visualize.py to ensure identical graph generation
    maze = [[0 for _ in range(cols)] for _ in range(rows)]
    start_r, start_c = 0, 0
    maze[start_r][start_c] = 1
    walls = []
    
    def add_walls(r, c):
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and maze[nr][nc] == 0:
                walls.append((nr, nc, r, c))
    
    add_walls(start_r, start_c)
    
    while walls:
        idx = random.randint(0, len(walls) - 1)
        wall_r, wall_c, from_r, from_c = walls.pop(idx)
        if maze[wall_r][wall_c] == 0:
            passages = 0
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = wall_r + dr, wall_c + dc
                if 0 <= nr < rows and 0 <= nc < cols and maze[nr][nc] == 1:
                    passages += 1
            if passages == 1:
                maze[wall_r][wall_c] = 1
                add_walls(wall_r, wall_c)
    
    maze[rows-1][cols-1] = 1
    
    # Add extra passages
    for _ in range(rows * cols // 4):
        r, c = random.randint(0, rows-1), random.randint(0, cols-1)
        maze[r][c] = 1
    
    graph = Graph(directed=True)
    def node_id(r, c): return r * cols + c
    
    nodes_map = {}
    for r in range(rows):
        for c in range(cols):
            if maze[r][c] == 1:
                uid = node_id(r, c)
                graph._nodes.add(uid)
                nodes_map[(r,c)] = uid
    
    for r in range(rows):
        for c in range(cols):
            if maze[r][c] == 1:
                uid = node_id(r, c)
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and maze[nr][nc] == 1:
                        nid = node_id(nr, nc)
                        graph.add_edge(uid, nid, 1.0)
                        
    return graph, node_id(0, 0)

def test_large_maze():
    print("Generating massive maze (30x40)...")
    graph, source = create_maze(30, 40)
    n = len(list(graph.nodes))
    print(f"Graph size: {n} nodes")
    
    print("Running Dijkstra (Reference)...")
    d_dist, d_prev = dijkstra(graph, source)
    
    reachable_count = sum(1 for d in d_dist.values() if d != float('inf'))
    print(f"Dijkstra found {reachable_count} reachable nodes")
    
    print("\nRunning Sorting Barrier Tracer...")
    tracer = SortingBarrierTracer(graph)
    sb_dist, sb_steps = tracer.run(source)
    
    # Check completeness
    sb_reachable = sum(1 for d in sb_dist.values() if d != float('inf'))
    print(f"Sorting Barrier found {sb_reachable} reachable nodes")
    
    if sb_reachable < reachable_count:
        print(f"❌ MISMATCH: Sorting Barrier missed {reachable_count - sb_reachable} nodes!")
    else:
        print("✅ Reachable count matches")

    # Check visited set in steps
    last_step = sb_steps[-1]
    visited_count = len(last_step.visited)
    print(f"Tracer 'visited' count: {visited_count}")
    
    if visited_count < reachable_count:
        print(f"⚠️  VISUALIZATION ISSUE: {reachable_count - visited_count} reachable nodes are not marked VISITED")
        
        # Analyze missed nodes
        missed = [u for u in d_dist if d_dist[u] != float('inf') and u not in last_step.visited]
        print(f"Sample missed nodes: {missed[:10]}")
        # Check their distances in SB
        missed_dists = [sb_dist.get(u, float('inf')) for u in missed]
        print(f"SB distances for missed nodes: {missed_dists[:10]}")

    print(f"\nTotal Steps: {len(sb_steps)}")

if __name__ == "__main__":
    test_large_maze()
