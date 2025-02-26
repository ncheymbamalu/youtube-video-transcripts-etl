.PHONE: install check clean pull process push etl
.DEFAULT_GOAL:=etl

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
	dvc pull

process:
	uv run python src/process.py

push:
	dvc add ./data
	git add data.dvc
	git commit -m "updating ./data locally and pushing to remote"; dvc push
	git push
	rm -rf data

etl: pull process push clean
