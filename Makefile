.PHONY: setup pipeline test lint api app qa

setup:
	python -m venv .venv
	.venv/bin/python -m pip install -r requirements.txt

pipeline:
	PYTHONPATH=Python/src .venv/bin/python -m customer_intelligence.pipeline

test:
	PYTHONPATH=Python/src .venv/bin/pytest

lint:
	.venv/bin/ruff check Python/src API App tests

api:
	.venv/bin/uvicorn API.main:app --reload

app:
	.venv/bin/streamlit run App/streamlit_app.py

qa: lint test

