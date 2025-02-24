.PHONY: install check clean pull push

install: pyproject.toml
	uv venv; source .venv/bin/activate
	uv sync

check:
	uv tool run isort src
	uv tool run ruff check src

clean:
	rm -rf `find . -type d -name __pycache__`
	rm -rf .ruff_cache

pull:
	uv run dvc pull

push:
	uv run dvc add ./data
	git add data.dvc
	git commit -m "updating ./data locally and pushing to remote"
	uv run dvc dvc push
	rm -rf ./data
