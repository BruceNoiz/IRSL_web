PYTHON ?= python3

.PHONY: help check check-source

help:
	@echo "make check  Run repository tests, Astro type checks, static builds and browsers (Python 3.9+, Node 22.12+, npm and Chromium installed)."
	@echo "make check-source  Run repository and source checks (Python standard library only)."

check:
	$(PYTHON) scripts/check.py

check-source:
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py' -v
