.ONESHELL:

.DEFAULT_GOAL := run

PORT = 8080
PYTHON = ./venv/bin/python3
PIP = ./venv/bin/pip3

venv/bin/activate: requirements.txt
	python -m venv venv
	chmod +x venv/bin/activate
	. ./venv/bin/activate
	$(PIP) install -r requirements.txt

venv: venv/bin/activate
	. venv/bin/activate

run: venv
	functions-framework --target=transcript_api --port $(PORT)

test:
	$(PYTHON) test.py -v

clean:
	rm -rf __pycache__
	rm -rf venv

