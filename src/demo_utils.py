# SSSP Algorithm Visualizer - Shared Logic
# Copyright (C) 2025  Asaf Kedar

import random
from typing import Tuple, Dict, Any, List

from graph import Graph
from algorithms.dijkstra import dijkstra
from visualization.tracer import generate_visualization_data

def create_sample_graph(n: int = 8, density: float = 0.4) -> Graph:
    """Create a random graph for visualization."""
    graph = Graph(directed=True)
    
    for i in range(n):
        graph._nodes.add(i)
    
    # Ensure connectivity from node 0
    for i in range(1, n):
        parent = random.randint(0, i - 1)
        weight = random.uniform(1, 10)
        graph.add_edge(parent, i, round(weight, 1))
    
    # Add additional random edges
    for i in range(n):
        for j in range(n):
            if i != j and random.random() < density:
                weight = random.uniform(1, 10)
                graph.add_edge(i, j, round(weight, 1))
    
    return graph

def create_maze(rows: int = 6, cols: int = 8) -> Tuple[Graph, Dict[str, Any], List[int]]:
    """
    Create a maze using randomized Prim's algorithm.
    Returns (graph, maze_info, shortest_path).
    """
    # Initialize grid - all walls
    # 0 = wall, 1 = passage
    maze = [[0 for _ in range(cols)] for _ in range(rows)]
    
    # Start from top-left
    start_r, start_c = 0, 0
    maze[start_r][start_c] = 1
    
    # Walls list: [(r, c, direction)]
    walls = []
    
    def add_walls(r, c):
        """Add neighboring walls to the list."""
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and maze[nr][nc] == 0:
                walls.append((nr, nc, r, c))
    
    add_walls(start_r, start_c)
    
    while walls:
        # Pick random wall
        idx = random.randint(0, len(walls) - 1)
        wall_r, wall_c, from_r, from_c = walls.pop(idx)
        
        # If the cell on the other side is a wall
        if maze[wall_r][wall_c] == 0:
            # Count adjacent passages
            passages = 0
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = wall_r + dr, wall_c + dc
                if 0 <= nr < rows and 0 <= nc < cols and maze[nr][nc] == 1:
                    passages += 1
            
            # Only carve if exactly one adjacent passage (to avoid loops initially)
            if passages == 1:
                maze[wall_r][wall_c] = 1
                add_walls(wall_r, wall_c)
    
    # Ensure bottom-right is reachable
    maze[rows-1][cols-1] = 1
    
    # Create additional passages for more interesting paths
    for _ in range(rows * cols // 4):
        r, c = random.randint(0, rows-1), random.randint(0, cols-1)
        maze[r][c] = 1
    
    # Build graph from maze
    graph = Graph(directed=True)
    
    def node_id(r, c):
        return r * cols + c
    
    # Add all passage cells as nodes
    for r in range(rows):
        for c in range(cols):
            if maze[r][c] == 1:
                graph._nodes.add(node_id(r, c))
    
    # Add edges between adjacent passages (bidirectional with weight 1)
    for r in range(rows):
        for c in range(cols):
            if maze[r][c] == 1:
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and maze[nr][nc] == 1:
                        # Weight based on distance (all 1 for uniform maze)
                        graph.add_edge(node_id(r, c), node_id(nr, nc), 1.0)
    
    source = node_id(0, 0)
    target = node_id(rows-1, cols-1)
    
    # Compute shortest path using Dijkstra
    dist, pred = dijkstra(graph, source)
    
    # Reconstruct path
    shortest_path = []
    if dist.get(target, float('inf')) < float('inf'):
        node = target
        while node is not None:
            shortest_path.append(node)
            node = pred.get(node)
        shortest_path.reverse()
    
    maze_info = {
        'rows': rows,
        'cols': cols,
        'grid': maze,
        'source': source,
        'target': target,
    }
    
    return graph, maze_info, shortest_path

class SSSPState:
    """Manages the graph state for visualization."""
    def __init__(self):
        self.current_graph = None
        self.current_source = 0
        random.seed(42)
        # Initialize with default
        print("Initializing graph...")
        self.reset_graph()
        
    def reset_graph(self):
        self.current_graph = create_sample_graph(n=8, density=0.3)
        self.current_source = 0
        
    def get_visualization_data(self) -> Dict[str, Any]:
        if self.current_graph is None:
            self.reset_graph()
        return generate_visualization_data(self.current_graph, self.current_source)
        
    def new_random_graph(self) -> Dict[str, Any]:
        n = random.randint(6, 12)
        density = random.uniform(0.2, 0.4)
        self.current_graph = create_sample_graph(n=n, density=density)
        self.current_source = 0
        return self.get_visualization_data()
        
    def new_maze(self, size_name: str = 'medium') -> Dict[str, Any]:
        sizes = {
            'small': (5, 6),
            'medium': (8, 10),
            'large': (12, 16),
            'huge': (20, 25),
            'massive': (30, 40),
        }
        rows, cols = sizes.get(size_name, (8, 10))
        
        self.current_graph, maze_info, shortest_path = create_maze(rows=rows, cols=cols)
        self.current_source = maze_info['source']
        
        data = self.get_visualization_data()
        data['maze'] = maze_info
        data['shortest_path'] = shortest_path
        return data

# Singleton instance for simple access
state = SSSPState()
