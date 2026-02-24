uvx ruff check ./src
uv run pytest -v --tb=short --cov=src --show-capture=no --capture=no  .\tests\
pause