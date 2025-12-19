# Makefile for setting up and running the Python SSSP project
# Used Chat GPT to help generate this Makefile.

PY ?= python3
VENV_DIR ?= .venv
PYTHON := $(VENV_DIR)/bin/python
PIP := $(VENV_DIR)/bin/pip
DEPS_STAMP := $(VENV_DIR)/.deps-installed

.PHONY: venv deps run matrix-run visualize test

venv: $(PYTHON)

$(PYTHON):
	$(PY) -m venv $(VENV_DIR)

deps: $(DEPS_STAMP)

$(DEPS_STAMP): requirements.txt | venv
	@if [ -f requirements.txt ]; then \
		$(PIP) install -r requirements.txt && touch $(DEPS_STAMP); \
	else \
		echo "No requirements.txt; skipping Python package install."; \
		touch $(DEPS_STAMP); \
	fi

# Run the CLI on an edge list file.
# Usage: make run GRAPH=path/to/edges.txt [SOURCE=0] [UNDIRECTED=1] [SHOW=1]
run: venv
	@if [ -z "$(GRAPH)" ]; then echo "GRAPH=<path to edge list> is required"; exit 1; fi
	PYTHONPATH=src $(PYTHON) app.py $(GRAPH) \
		$(if $(SOURCE),--source $(SOURCE),) \
		$(if $(UNDIRECTED),--undirected,) \
		$(if $(SHOW),--show-distances,)

# Quick demo using the built-in adjacency matrix (prints both algorithms).
matrix-run: venv
	PYTHONPATH=src $(PYTHON) scripts/matrix_demo.py

# Launch the interactive algorithm visualizer (opens in browser).
visualize: deps
	PYTHONPATH=src $(PYTHON) visualize.py

# Run correctness tests for the Sorting Barrier SSSP algorithm.
test: venv
	PYTHONPATH=src $(PYTHON) scripts/test_sorting_barrier.py
