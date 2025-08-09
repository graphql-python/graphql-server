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

You can check the tests coverage by adding the `--cov` and `--cov-report=term-missing` (to report the missing lines in the command output) flags from `pytest-cov` when running `pytest`.

```bash
uv run pytest --cov --cov-report=term-missing
```

## Before commiting

All files must be properly formatted before creating a PR, so we can merge it upstream.

You can run `ruff` for formatting automatically all the files of the project:

```bash
uv run ruff format
```
