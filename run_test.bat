uvx ruff check ./src
uv run pytest -v --cov=src --show-capture=no --capture=no  --full-trace .\tests\
pause