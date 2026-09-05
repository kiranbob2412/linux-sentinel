PYTHON ?= python3
export PYTHONPATH := $(CURDIR)/src

.PHONY: test lint scan build clean

test:
	$(PYTHON) -m unittest discover -s tests -v

lint:
	$(PYTHON) -m compileall -q src tests
	@bash -n scripts/install.sh scripts/uninstall.sh
	@if command -v shellcheck >/dev/null 2>&1; then shellcheck scripts/*.sh bin/linuxops-sentinel; else echo "shellcheck not installed; skipped"; fi

scan:
	$(PYTHON) -m linuxops_sentinel scan --format table

build:
	$(PYTHON) -m pip wheel --no-deps --no-build-isolation --wheel-dir dist .

clean:
	rm -rf build dist .coverage src/*.egg-info src/linuxops_sentinel/__pycache__ tests/__pycache__