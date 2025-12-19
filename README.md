# SSSP Algorithm Visualizer & Benchmarker

This project is a comprehensive visualization and benchmarking tool for Single-Source Shortest Path (SSSP) algorithms, specifically comparing the classic **Dijkstra's Algorithm** against the modern **Sorting Barrier SSSP** algorithm.

The implementations are based on the paper *"Breaking the Sorting Barrier for Directed Single-Source Shortest Paths"* by Ran Duan et al. (arXiv:2504.17033v2).

## Visualizer Features

The project includes a rich, interactive web-based visualizer designed to provide deep insights into how these algorithms differ in execution.

### Interactive Web UI
*   **Split-Screen Comparison**: Watch both algorithms run side-by-side on the same graph instance.
*   **Step-by-Step Execution**: Control execution flow with Play, Pause, Step Forward, and Step Back controls.
*   **Variable Speed**: Adjust playback speed from 1x to 150x.
*   **Real-time Metrics**: Track the "Sorting Cost" and "Steps" for each algorithm in real-time.

### 🏁 Race Mode
A unique feature that visualizing the *theoretical* asymptotic speedup of the Sorting Barrier algorithm.
*   **Concept**: Instead of advancing one logical step at a time, algorithms advance based on their theoretical work accumulation.
*   **Dijkstra**: Advances by "paying" $O(\log n)$ cost per heap operation.
*   **Sorting Barrier**: Advances by "paying" $O(\sqrt{\log n})$ cost per operation (thanks to the Partial Sort data structure).
*   **Visual Result**: You can visually see the Sorting Barrier algorithm "overtaking" Dijkstra on larger graphs as its lower asymptotic complexity allows it to process more nodes for the same amount of "computational budget".

### Maze & Graph Generation
*   **Maze Generation**: Generate randomized mazes (using Prim's algorithm) to see how the algorithms navigate geometric constraints.
*   **Random Graphs**: Create random directed graphs with customizable size and density settings.
*   **Presets**: Quickly switch between graph sizes from "Small" (5x6) to "Massive" (30x40).

## CLI Features

For performance analysis on larger datasets, the project includes a Command Line Interface (CLI).
*   **Benchmarking**: Measure precise runtime execution times (in milliseconds) for both algorithms.
*   **Correctness Verification**: Automatically compares the output distances of both algorithms to ensure correctness (reporting any mismatches).
*   **Large Graph Support**: Capable of handling graph sizes that are too large for the visualizer.

## Installation

1.  **Prerequisites**: Ensure you have Python 3.8+ installed.
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Web Visualization
To start the interactive visualizer:
```bash
python visualize.py
```
Then open your browser and navigate to: [http://localhost:8080](http://localhost:8080)

### CLI Benchmarking
To run a comparison on a specific graph file:
```bash
python app.py path/to/graph.txt
```

**Options**:
*   `--undirected`: Treat the graph as undirected (default is directed).
*   `--source <id>`: Specify a source node ID.
*   `--show-distances`: Print the final distance map (recommended only for small graphs).

**Input Format**:
The graph file should differ an edge list where each line is `u v [weight]`:
```text
0 1 5.2
1 2 3.0
...
```

## Implementation Details

### Sorting Barrier SSSP Algorithm
The core innovation of this project is the implementation of the **Sorting Barrier SSSP** algorithm (Duan et al., 2025). This algorithm breaks the classic $O(m \log n)$ barrier for Dijkstra's algorithm by carefully managing dependencies to avoid full sorting.

#### Key Concepts
1.  **Bounded Multi-Source Shortest Path (BMSSP)**:
    Instead of a global priority queue, the algorithm solves a recursive subproblem: given a set of sources $S$ and a distance bound $B$, compute shortest paths from $S$ up to distance $B$.
    *   **Parameters**:
        *   $k = \log^{1/3} n$: Controls the branching factor.
        *   $t = \log^{2/3} n$: Controls the block size growth ($M = 2^{lt}$).
    *   **Logic**: The recursion depth is bounded by $\log n / t = \log^{1/3} n$. At each level, it processes vertices in blocks, using pivots to break cyclic dependencies.

2.  **FindPivots (Algorithm 1)**:
    To handle cyclic dependencies without a global heap, the algorithm identifies "Pivot" vertices.
    *   It runs $k$ rounds of Bellman-Ford-style relaxation.
    *   It builds an "Equality Subgraph" of tight edges.
    *   Vertices that are roots of large trees ($\ge k$ nodes) in this subgraph become **Pivots**.
    *   These pivots are safe to process using the Partial Sort structure.

3.  **Base Case (Algorithm 2)**:
    When the recursion bottoms out (or for small sets of vertices), it switches to a bounded version of Dijkstra's algorithm.
    *   It only explores up to $k+1$ vertices.
    *   This limits the heap size and operations, keeping the cost manageable ($O(k \log k)$ per call).

### Partial Sort Data Structure
The algorithm's speedup relies on a novel **Partial Sort** data structure (Lemma 3.3 in the paper).

*   **Problem**: Standard heaps cost $O(\log n)$ per extract-min.
*   **Solution**: We don't need *total* order, just the "next batch" of smallest elements.
*   **Mechanism**:
    *   The structure maintains elements in an unsorted list.
    *   **`Pull()`**: When finding the next set of vertices to process, it uses **Quickselect** (linear-time selection) to find the smallest $M$ elements in $O(M)$ time.
    *   **Efficiency**: This avoids the $O(\log n)$ sorting bottleneck, replacing it with an amortized cost that approaches $O(\sqrt{\log n})$ per edge operations.

### Dijkstra's Algorithm
A highly optimized baseline implementation using Python's standard `heapq` module.
*   **Binary Heap**: Provides $O(\log n)$ insertion and extraction.
*   **Decrease-Key**: Simulated using "lazy deletion" (pushing a new entry and ignoring stale ones on extraction), which is a standard practical optimization in Python.

## Limitations

*   **Theoretical vs. Practical Performance**: The Sorting Barrier algorithm is *theoretically* faster ($o(\log n)$ per op) asymptotically. However, in practice, for the graph sizes supported by this Python implementation, the high constant factors and overhead of the complex recursive structure often make it slower than the highly optimized, simple Dijkstra loop. The "Race Mode" in the visualizer is designed precisely to demonstrate the *potential* speedup by simulating the asymptotic costs.
*   **Edge Weights**: Currently supports **non-negative edge weights** only.
*   **Graph Size (Visualizer)**: The web visualization is optimized for small to medium graphs (up to ~1000 nodes) for UI responsiveness. For larger graphs, use the CLI.
*   **Recursion Depth**: The algorithm is recursive; extremely deep recursion on massive graphs might hit Python's recursion limit (though the algorithm's depth is logarithmic, so this is rarely an issue).

## License

This project is licensed under the GNU General Public License v3.0 (GPLv3). See the [COPYING](COPYING) file for details.

