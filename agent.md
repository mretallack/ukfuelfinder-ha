# Agent Instructions & CI Quality Checks

Before committing or pushing any code changes, ensure all linting and test checks pass locally:

1. **Format with Black**:
   ```bash
   ./venv/bin/black custom_components tests
   ```

2. **Sort Imports with isort**:
   ```bash
   ./venv/bin/isort custom_components tests
   ```

3. **Run Tests**:
   ```bash
   PYTHONPATH=. ./venv/bin/pytest --ignore=tests/test_integration_simple.py
   ```

Always ensure `black --check` and `isort --check-only` pass before pushing to remote repository to guarantee CI success.
