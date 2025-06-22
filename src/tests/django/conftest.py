from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from graphql_server.django.test import GraphQLTestClient


@pytest.fixture
def graphql_client() -> GraphQLTestClient:
    from django.test.client import Client

    from graphql_server.django.test import GraphQLTestClient

    return GraphQLTestClient(Client())
