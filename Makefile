lint:
	poetry run black .
	poetry run ruff check .
	poetry run mypy .

test:
	poetry run pytest

debug:
	poetry build -f wheel
	poetry self remove poetry-plugin-lockedbuild
	poetry self add `pwd`/dist/poetry_plugin_lockedbuild*.whl
	poetry lockedbuild
	yes | unzip `pwd`/dist/poetry_plugin_lockedbuild*.whl -d dist/

all: lint test