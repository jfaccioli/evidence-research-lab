# Crypto Research Lab — operator shortcuts
# Usage: make doctor | make status | make programmes

export PYTHONPATH := src
PY ?= .venv/bin/python

.PHONY: doctor status programmes inventory fetch-1d fetch-4h test paper-smoke check

doctor:
	$(PY) -m crl doctor

status:
	$(PY) -m crl status

programmes:
	$(PY) -m crl programmes

inventory:
	$(PY) -m crl programmes --write-md

fetch-1d:
	$(PY) -m crl fetch --interval 1d

fetch-4h:
	$(PY) -m crl fetch --interval 4h

test:
	$(PY) -m pytest tests/ -q --tb=line

check: doctor test status

paper-smoke:
	$(PY) -m crl paper -H examples/batch/hyp_sma200_long.yaml --cash 50

# Example: make run-prog PROG=fade
run-prog:
	$(PY) -m crl run-programme examples/batch/$(PROG)

# Example: make autopsy PROG=fade
autopsy:
	$(PY) -m crl autopsy examples/batch/$(PROG)
