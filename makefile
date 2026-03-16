# Detect OS
UNAME := $(shell uname -s 2>/dev/null || echo Windows_NT)

# Normalize OS name to "Windows_NT" for all Windows environments
ifeq ($(findstring MINGW,$(UNAME)),MINGW)
    OS := Windows_NT
else
    OS := $(UNAME)
endif

# Common variables
PYTHONFILES = $(shell ls *.py 2>/dev/null || dir /B *.py)
PYTESTFLAGS = -vv --cov=app --cov-report=html
TEST_CMD = pytest $(PYTESTFLAGS) tests/

# Our directories
API_DIR = app
REQ_DIR = .
VENV_DIR = .venv

# Platform-specific variables
ifeq ($(OS), Windows_NT)
    ACTIVATE = . $(VENV_DIR)/Scripts/activate
else
    ACTIVATE = . $(VENV_DIR)/bin/activate
endif

ifeq (, $(shell which python))
    PYTHON_CREATE = python3
else
    PYTHON_CREATE = python
endif

dev_env:
	@if [ ! -d $(VENV_DIR) ]; then \
		$(PYTHON_CREATE) -m venv $(VENV_DIR); \
	fi; \
	$(ACTIVATE) && pip install --upgrade pip setuptools wheel && pip install -r $(REQ_DIR)/requirements-dev.txt && pip install pytest pytest-cov

pytests: 
	$(ACTIVATE) && $(TEST_CMD)

tests: pytests

run_local_server: tests
	$(ACTIVATE) && FLASK_APP=app flask run --debug --host=0.0.0.0 --port=8000

clean:
	rm -rf $(VENV_DIR) .pytest_cache htmlcov .coverage
