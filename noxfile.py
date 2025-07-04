import itertools
from typing import Any, Callable

import nox
from nox import Session, session

nox.options.default_venv_backend = "uv|virtualenv"
# nox.options.reuse_existing_virtualenvs = True
# nox.options.error_on_external_run = True
# nox.options.default_venv_backend = "uv"

PYTHON_VERSIONS = ["3.13", "3.12", "3.11", "3.10", "3.9"]

GQL_CORE_VERSIONS = [
    "3.3.0a9",
    "3.2.3",
]

COMMON_PYTEST_OPTIONS = [
    "--cov=.",
    "--cov-append",
    "--cov-report=xml",
    "-n",
    "auto",
    "--showlocals",
    "-vv",
    "--ignore=tests/typecheckers",
    "--ignore=tests/cli",
    "--ignore=tests/benchmarks",
    "--ignore=tests/experimental/pydantic",
]

INTEGRATIONS = [
    "asgi",
    "aiohttp",
    "chalice",
    "channels",
    "django",
    "fastapi",
    "flask",
    "webob",
    "quart",
    "sanic",
    "litestar",
    "pydantic",
]


def _install_gql_core(session: Session, version: str) -> None:
    session.install(f"graphql-core=={version}")


gql_core_parametrize = nox.parametrize(
    "gql_core",
    GQL_CORE_VERSIONS,
)


def with_gql_core_parametrize(name: str, params: list[str]) -> Callable[[Any], Any]:
    # github cache doesn't support comma in the name, this is a workaround.
    arg_names = f"{name}, gql_core"
    combinations = list(itertools.product(params, GQL_CORE_VERSIONS))
    ids = [f"{name}-{comb[0]}__graphql-core-{comb[1]}" for comb in combinations]
    return lambda fn: nox.parametrize(arg_names, combinations, ids=ids)(fn)


@session(python=PYTHON_VERSIONS, name="Tests", tags=["tests"])
@gql_core_parametrize
def tests(session: Session, gql_core: str) -> None:
    session.run_always("uv", "sync", "--group", "dev", external=True)
    session.run_always("uv", "sync", "--group", "integrations", external=True)
    _install_gql_core(session, gql_core)
    markers = (
        ["-m", f"not {integration}", f"--ignore=tests/{integration}"]
        for integration in INTEGRATIONS
    )
    markers = [item for sublist in markers for item in sublist]

    session.run(
        "uv",
        "run",
        "pytest",
        "--ignore",
        "tests/websockets/test_graphql_ws.py",
        *COMMON_PYTEST_OPTIONS,
        *markers,
    )


@session(python=["3.12"], name="Django tests", tags=["tests"])
@with_gql_core_parametrize("django", ["5.1.3", "5.0.9", "4.2.0"])
def tests_django(session: Session, django: str, gql_core: str) -> None:
    session.run_always("uv", "sync", "--group", "dev", external=True)
    session.run_always("uv", "sync", "--group", "integrations", external=True)

    _install_gql_core(session, gql_core)
    session.install(f"django~={django}")  # type: ignore
    session.install("pytest-django")  # type: ignore

    session.run("uv", "run", "pytest", *COMMON_PYTEST_OPTIONS, "-m", "django")


@session(python=["3.11"], name="Starlette tests", tags=["tests"])
@gql_core_parametrize
def tests_starlette(session: Session, gql_core: str) -> None:
    session.run_always("uv", "sync", "--group", "dev", external=True)
    session.run_always("uv", "sync", "--group", "integrations", external=True)

    session.install("starlette")  # type: ignore
    _install_gql_core(session, gql_core)
    session.run("uv", "run", "pytest", *COMMON_PYTEST_OPTIONS, "-m", "asgi")


@session(python=["3.11"], name="Test integrations", tags=["tests"])
@with_gql_core_parametrize(
    "integration",
    [
        "aiohttp",
        "chalice",
        "channels",
        "fastapi",
        "flask",
        "webob",
        "quart",
        "sanic",
        "litestar",
    ],
)
def tests_integrations(session: Session, integration: str, gql_core: str) -> None:
    session.run_always("uv", "sync", "--group", "dev", external=True)
    session.run_always("uv", "sync", "--group", "integrations", external=True)

    session.install(integration)  # type: ignore
    _install_gql_core(session, gql_core)
    if integration == "aiohttp":
        session.install("pytest-aiohttp")  # type: ignore
    elif integration == "channels":
        session.install("pytest-django")  # type: ignore
        session.install("daphne")  # type: ignore

    session.run("uv", "run", "pytest", *COMMON_PYTEST_OPTIONS, "-m", integration)
