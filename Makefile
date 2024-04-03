clean: clean-build clean-pyc clean-test ## remove all build, docs, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	@echo "> Clean Build Artifacts"
	@rm -fr build/
	@rm -fr dist/
	@rm -fr .eggs/
	@find . \( -path ./env -o -path ./venv -o -path ./.env -o -path ./.venv \) -prune -o -name '*.egg-info' -exec rm -fr {} +
	@find . \( -path ./env -o -path ./venv -o -path ./.env -o -path ./.venv \) -prune -o -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	@echo "> Clean Python Artifacts"
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +
	@find . -name '*~' -exec rm -f {} +
	@find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	@echo "> Clean Tests"
	@rm -f .coverage
	@rm -fr htmlcov/
	@rm -fr .pytest_cache
	@rm -fr .mypy_cache

format: # Format code with black and isort
	@echo ">> Formatting with black"
	@black .
	@echo ">> Formatting with isort"
	@isort src
	@isort tests

lint: # Linting with flake8 and type checking with mypy
	@echo ">> Linting with flake8"
	@flake8 src
	@flake8 tests
	@echo ">> Type Checking with mypy"
	@mypy --install-types --non-interactive --ignore-missing-imports --disallow-untyped-defs src
	@mypy --install-types --non-interactive --ignore-missing-imports --disallow-untyped-defs tests

notice:
	@echo "> Fill NOTICE"
	@pigar generate
	@liccheck -s liccheck_strategy.ini
	@pip-licenses --from=mixed > NOTICE

security:
	@echo "> Check Security"
	@pip-audit -s osv --local --desc=on

test: clean
	@echo "> Pass Tests"
	@pytest . --junitxml=build/reports/tests.xml --cov=src/matbexp --cov-report=term-missing --cov-report=xml:build/reports/coverage.xml --cov-report=html:build/reports/cov --cov-branch -rsx
	@xdoctest matbexp
