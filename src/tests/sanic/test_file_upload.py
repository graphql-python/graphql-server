from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING

import pytest
from graphql import (
    GraphQLArgument,
    GraphQLField,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLSchema,
    GraphQLString,
)

from graphql_server.sanic import utils
from graphql_server.sanic.views import GraphQLView
from sanic import Sanic
from sanic.request import File

UploadScalar = GraphQLScalarType(
    name="Upload",
    description="The `Upload` scalar type represents a file upload.",
    serialize=lambda f: f,
    parse_value=lambda f: f,
    parse_literal=lambda *_: None,
)


def resolve_index(_root, _info):
    return "Hello there"


Query = GraphQLObjectType(
    name="Query",
    fields={
        "index": GraphQLField(
            GraphQLNonNull(GraphQLString),
            resolve=resolve_index,
        )
    },
)


def resolve_file_upload(_root, _info, file):
    return file.name


Mutation = GraphQLObjectType(
    name="Mutation",
    fields={
        "fileUpload": GraphQLField(
            GraphQLNonNull(GraphQLString),
            args={
                "file": GraphQLArgument(GraphQLNonNull(UploadScalar)),
            },
            resolve=resolve_file_upload,
        )
    },
)

if TYPE_CHECKING:
    from sanic import Sanic as SanicApp


@pytest.fixture
def app() -> SanicApp:
    sanic_app = Sanic("sanic_testing")

    schema = GraphQLSchema(query=Query, mutation=Mutation)

    sanic_app.add_route(
        GraphQLView.as_view(
            schema=schema,
            multipart_uploads_enabled=True,
        ),
        "/graphql",
    )

    return sanic_app


def test_file_cast(app: Sanic):
    """Tests that the list of files in a sanic Request gets correctly turned into a dictionary"""
    file_name = "test.txt"
    file_content = b"Hello, there!."
    in_memory_file = BytesIO(file_content)
    in_memory_file.name = file_name

    form_data = {
        "operations": '{ "query": "mutation($file: Upload!){ fileUpload(file: $file) }", "variables": { "file": null } }',
        "map": '{ "file": ["variables.file"] }',
    }
    files = {"file": in_memory_file}

    request, _ = app.test_client.post("/graphql", data=form_data, files=files)

    files_dict = utils.convert_request_to_files_dict(request)  # type: ignore
    file = files_dict["file"]

    assert isinstance(file, File)
    assert file.name == file_name
    assert file.body == file_content


def test_endpoint(app: Sanic):
    """Tests that the graphql api correctly handles file upload and processing"""
    file_name = "test.txt"
    file_content = b"Hello, there!"
    in_memory_file = BytesIO(file_content)
    in_memory_file.name = file_name

    form_data = {
        "operations": '{ "query": "mutation($file: Upload!){ fileUpload(file: $file) }", "variables": { "file": null } }',
        "map": '{ "file": ["variables.file"] }',
    }
    files = {"file": in_memory_file}

    _, response = app.test_client.post("/graphql", data=form_data, files=files)

    assert response.json["data"]["fileUpload"] == file_name  # type: ignore
