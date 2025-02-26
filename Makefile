.PHONE: install check clean pull etl push
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
	dvc pull

etl:
	uv run python src/etl.py

push:
	dvc add ./data
	git add data.dvc
	git commit -m "updating ./data locally and pushing to remote"; dvc push
	git push
	rm -rf data

runner: pull etl push clean
