.PHONY: install check clean pull etl push runner
.DEFAULT_GOAL:=runner

install: pyproject.toml
	uv venv; source .venv/bin/activate
	uv sync

check:
	uv tool run isort src
	uv tool run ruff check src

clean:
	rm -rf `find . -type d -name __pycache__`
	rm -rf .ruff_cache
	rm -rf logs

pull:
	uv run dvc pull

etl:
	uv run python src/etl.py 

push:
	uv run dvc add ./data
	git config user.name "github-actions"; git config user.email "github-actions@github.com"
	git add data.dvc
	git commit -m "updating ./data locally and pushing to remote"; uv run dvc push
	git push
	rm -rf data

runner: pull etl push clean
