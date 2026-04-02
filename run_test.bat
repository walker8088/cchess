uvx ruff check ./src
uv run python -m pytest -v --tb=short --cov=src --show-capture=no --capture=no  .\tests\
pause