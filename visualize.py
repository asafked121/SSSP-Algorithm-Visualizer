#!/usr/bin/env python3
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
SSSP Algorithm Visualizer - Web Server

Run this script to start the visualization server, then open
http://localhost:5000 in your browser to watch both algorithms.

Usage:
    python visualize.py
    # or
    make visualize
"""

import json
import random
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from flask import Flask, send_from_directory, jsonify

from graph import Graph
from visualization.tracer import generate_visualization_data

app = Flask(__name__, static_folder='static')

# Global graph state
current_graph = None
current_source = 0


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


def create_maze(rows: int = 6, cols: int = 8) -> tuple:
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
    from algorithms.dijkstra import dijkstra
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


def init_graph():
    """Initialize the default graph."""
    global current_graph, current_source
    random.seed(42)
    current_graph = create_sample_graph(n=8, density=0.3)
    current_source = 0


@app.route('/')
def index():
    """Serve the main HTML page."""
    return send_from_directory('static', 'index.html')


@app.route('/api/visualization')
def get_visualization():
    """Get visualization data for current graph."""
    global current_graph, current_source
    
    if current_graph is None:
        init_graph()
    
    data = generate_visualization_data(current_graph, current_source)
    return jsonify(data)


@app.route('/api/new-graph', methods=['POST'])
def new_graph():
    """Generate a new random graph."""
    global current_graph, current_source
    
    n = random.randint(6, 12)
    density = random.uniform(0.2, 0.4)
    current_graph = create_sample_graph(n=n, density=density)
    current_source = 0
    
    data = generate_visualization_data(current_graph, current_source)
    return jsonify(data)


@app.route('/api/maze', methods=['POST'])
def maze():
    """Generate a maze and return visualization data."""
    global current_graph, current_source
    
    from flask import request
    
    # Get size from request
    req_data = request.get_json() or {}
    size = req_data.get('size', 'medium')
    
    # Size presets
    sizes = {
        'small': (5, 6),
        'medium': (8, 10),
        'large': (12, 16),
        'huge': (20, 25),
        'massive': (30, 40),
    }
    
    rows, cols = sizes.get(size, (8, 10))
    
    current_graph, maze_info, shortest_path = create_maze(rows=rows, cols=cols)
    current_source = maze_info['source']
    
    data = generate_visualization_data(current_graph, current_source)
    data['maze'] = maze_info
    data['shortest_path'] = shortest_path
    
    return jsonify(data)


def main():
    """Run the visualization server."""
    print("=" * 60)
    print("⚡ SSSP Algorithm Visualizer")
    print("=" * 60)
    print()
    print("Starting server...")
    print()
    print("Open your browser to: http://localhost:8080")
    print()
    print("Controls:")
    print("  • Reset    - Reset both algorithms to step 0")
    print("  • Step     - Advance both algorithms by one step")
    print("  • Play     - Auto-play the visualization")
    print("  • Speed    - Adjust playback speed")
    print("  • New Graph - Generate a new random graph")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    init_graph()
    app.run(debug=False, host='0.0.0.0', port=8080)


if __name__ == '__main__':
    main()

