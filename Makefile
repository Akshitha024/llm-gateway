.PHONY: install lint fmt typecheck test bench serve pdf clean

install:
	uv sync --extra dev

lint:
	uv run ruff check src tests
	uv run ruff format --check src tests

fmt:
	uv run ruff format src tests
	uv run ruff check --fix src tests

typecheck:
	uv run mypy src

test:
	uv run pytest -v

bench:
	uv run lgw bench --out-dir runs/latest --n 10000

serve:
	uv run lgw serve --host 0.0.0.0 --port 8000

pdf:
	cd docs/_report && pandoc research_report.md \
	    -o ../research_report.pdf --pdf-engine=xelatex --toc --toc-depth=2 \
	    --number-sections -V geometry:margin=1in -V fontsize=11pt \
	    -V mainfont="Helvetica" -V monofont="Menlo" \
	    -V linkcolor=blue -V urlcolor=blue -V linestretch=1.15 \
	    || echo "pandoc + xelatex required"

clean:
	rm -rf runs/* .pytest_cache .mypy_cache .ruff_cache
