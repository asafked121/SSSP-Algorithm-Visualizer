// SSSP Algorithm Visualizer - Pyodide Bridge
// Copyright (C) 2025 Asaf Kedar

let pyodide = null;
let pyodideReady = false;

// Files to load into Pyodide's filesystem
// Paths are relative to the root of the serving directory (assuming static/index.html is entry)
// If serving from root, we access ../src
const PYTHON_FILES = [
    'visualization/__init__.py',
    'visualization/tracer.py',
    'datastructures/partial_sort.py',
    'datastructures/partial_priority.py',
    'graph.py',
    'algorithms/dijkstra.py',
    'algorithms/sorting_barrier_sssp.py',
    'demo_utils.py',
    'data/adjacency_matrix.py'
];

async function initPyodideEnvironment() {
    if (pyodideReady) return;

    console.log('Loading Pyodide...');
    const statusMsg = document.getElementById('dijkstra-message');
    if (statusMsg) statusMsg.textContent = 'Loading Python runtime...';

    pyodide = await loadPyodide();

    console.log('Loading Python files...');
    if (statusMsg) statusMsg.textContent = 'Downloading visualization logic...';

    // Create directory structure
    pyodide.runPython(`
        import os
        os.makedirs('src/algorithms', exist_ok=True)
        os.makedirs('src/datastructures', exist_ok=True)
        os.makedirs('src/visualization', exist_ok=True)
        os.makedirs('src/data', exist_ok=True)
        import sys
        sys.path.insert(0, os.getcwd() + '/src')
    `);

    // Fetch and write files
    for (const file of PYTHON_FILES) {
        try {
            // ".." because we are in static/ and src/ is sibling
            const response = await fetch('../src/' + file);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const code = await response.text();

            // Write to Pyodide FS
            pyodide.FS.writeFile('src/' + file, code);
            console.log(`Loaded ${file}`);
        } catch (e) {
            console.error(`Failed to load ${file}:`, e);
            if (statusMsg) statusMsg.textContent = `Error loading ${file}`;
            throw e;
        }
    }

    // Initialize state
    console.log('Initializing graph...');
    pyodide.runPython(`
        from demo_utils import state
        # Initial graph generation happens in demo_utils on import/init
        print("Python backend ready.")
    `);

    pyodideReady = true;
    if (statusMsg) statusMsg.textContent = 'Python Ready. Loading Graph...';
    console.log('Pyodide interface ready.');
}

// --- API Wrappers ---

async function pyGetVisualization() {
    if (!pyodideReady) await initPyodideEnvironment();
    const result = pyodide.runPython(`
        import json
        json.dumps(state.get_visualization_data())
    `);
    return JSON.parse(result);
}

async function pyNewGraph() {
    if (!pyodideReady) await initPyodideEnvironment();
    const result = pyodide.runPython(`
        import json
        json.dumps(state.new_random_graph())
    `);
    return JSON.parse(result);
}

async function pyGenerateMaze(size) {
    if (!pyodideReady) await initPyodideEnvironment();
    // Pass 'size' as a variable
    pyodide.globals.set("req_size", size);
    const result = pyodide.runPython(`
        import json
        json.dumps(state.new_maze(req_size))
    `);
    return JSON.parse(result);
}
