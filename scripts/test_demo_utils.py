
import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'src'))

from demo_utils import state

print("Testing get_visualization_data...")
data = state.get_visualization_data()
assert 'graph' in data
print("OK")

print("Testing new_random_graph...")
data2 = state.new_random_graph()
assert data2['graph']['nodes'] != data['graph']['nodes'] or len(data2['graph']['nodes']) > 0
print("OK")

print("Testing new_maze...")
maze_data = state.new_maze('small')
assert 'maze' in maze_data
assert 'shortest_path' in maze_data
print("OK")

print("All demo_utils tests passed.")
