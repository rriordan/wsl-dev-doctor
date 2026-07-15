.PHONY: check test run

check:
	uv run ruff format --check .
	uv run ruff check .
	uv run mypy src

test:
	uv run pytest

run:
	uv run wsl-doctor --format markdown --output -
