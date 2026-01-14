.PHONY: install build-testhelpers test test-verbose test-smoke test-standard test-full clean clean-exports help

# Optional: append --keep-inboxes by running: make test-smoke KEEP_INBOXES=1
PYTEST_OPTS := $(if $(KEEP_INBOXES),--keep-inboxes,)

# Default target
help:
	@echo "client-interop - Cross-SDK integration tests"
	@echo ""
	@echo "Targets:"
	@echo "  install        Install Python dependencies"
	@echo "  build-testhelpers  Build SDK testhelpers across repos"
	@echo "  test           Run all interop tests"
	@echo "  test-verbose   Run tests with verbose output"
	@echo "  test-smoke     Quick smoke test (~5 tests)"
	@echo "  test-standard  Standard coverage (~10 cross-SDK + 5 decrypt tests)"
	@echo "  test-full      Full matrix (~20 cross-SDK + 5 decrypt tests)"
	@echo "  clean          Remove generated files"
	@echo "  clean-exports  Clear saved inbox exports"
	@echo ""
	@echo "Options:"
	@echo "  KEEP_INBOXES=1  Keep test inboxes after run (e.g., make test-smoke KEEP_INBOXES=1)"
	@echo ""
	@echo "Environment variables:"
	@echo "  VAULTSANDBOX_URL      Server URL"
	@echo "  VAULTSANDBOX_API_KEY  API key"
	@echo "  CLIENT_GO_PATH        Path to client-go repo"
	@echo "  CLIENT_NODE_PATH      Path to client-node repo"
	@echo "  CLIENT_PYTHON_PATH    Path to client-python repo"

install:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

build-testhelpers:
	./scripts/build_testhelpers.sh

test:
	PYTHONPATH=tests .venv/bin/pytest $(PYTEST_OPTS)

test-verbose:
	PYTHONPATH=tests .venv/bin/pytest -v --tb=long $(PYTEST_OPTS)

test-smoke:
	PYTHONPATH=tests .venv/bin/pytest --level=smoke $(PYTEST_OPTS)

test-standard:
	PYTHONPATH=tests .venv/bin/pytest --level=standard $(PYTEST_OPTS)

test-full:
	PYTHONPATH=tests .venv/bin/pytest --level=full $(PYTEST_OPTS)

clean:
	rm -rf __pycache__ .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

clean-exports:
	rm -f exports/*.json
