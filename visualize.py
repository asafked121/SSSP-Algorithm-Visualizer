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

from flask import Flask, send_from_directory, jsonify, request
from demo_utils import state

app = Flask(__name__, static_folder='static')

@app.route('/')
def index():
    """Serve the main HTML page."""
    return send_from_directory('static', 'index.html')


@app.route('/api/visualization')
def get_visualization():
    """Get visualization data for current graph."""
    return jsonify(state.get_visualization_data())


@app.route('/api/new-graph', methods=['POST'])
def new_graph():
    """Generate a new random graph."""
    return jsonify(state.new_random_graph())


@app.route('/api/maze', methods=['POST'])
def maze():
    """Generate a maze and return visualization data."""
    # Get size from request
    req_data = request.get_json() or {}
    size = req_data.get('size', 'medium')
    
    return jsonify(state.new_maze(size))


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
    
    app.run(debug=False, host='0.0.0.0', port=8080)


if __name__ == '__main__':
    main()

