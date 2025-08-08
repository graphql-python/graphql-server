# Agent Instructions

This repository provides a base library for building GraphQL servers across multiple Python web frameworks.

## Project Structure
- `src/graphql_server/` contains the library implementation.
- `src/tests/` houses the unit tests.
- `docs/` includes framework-specific documentation.
- `pyproject.toml` defines project metadata and dependencies.
- `noxfile.py` holds automation sessions for linting and testing.

## Running Tests

Run the full test suite with:

```bash
uv run pytest
```

You can check the tests coverage by adding the `--cov` flag from `pytest-cov` when running `pytest`.

```bash
uv run pytest --cov
```
