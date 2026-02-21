EXAMPLE ?= quickstart

.PHONY: setup test test-all clean

setup:
	cd $(EXAMPLE) && uv sync

test:
	cd $(EXAMPLE) && uv run pytest -v

test-all:
	@for dir in */; do \
		if [ -f "$$dir/pyproject.toml" ]; then \
			echo "--- $$dir ---"; \
			(cd "$$dir" && uv sync && uv run pytest -v) || exit 1; \
		fi; \
	done

clean:
	fd -t d -H '.venv' -x rm -rf {}
	fd -t d '__pycache__' -x rm -rf {}
	fd -t d '.egg-info' -x rm -rf {}
