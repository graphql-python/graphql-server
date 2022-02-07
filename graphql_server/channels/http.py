"""GraphQLHTTPHandler
A consumer to provide a graphql endpoint, and optionally graphiql.
"""
import json
from pathlib import Path
from typing import Any, Optional

from channels.generic.http import AsyncHttpConsumer

from graphql import GraphQLSchema, ExecutionResult


class GraphQLHttpConsumer(AsyncHttpConsumer):
    """
    A consumer to provide a view for GraphQL over HTTP.
    To use this, place it in your ProtocolTypeRouter for your channels project:

    ```
    from graphql_ws.channels import GraphQLHttpConsumer
    from channels.routing import ProtocolTypeRouter, URLRouter
    from django.core.asgi import get_asgi_application
    application = ProtocolTypeRouter({
      "http": URLRouter([
        re_path("^graphql", GraphQLHttpConsumer(schema=schema)),
        re_path("^", get_asgi_application()),
      ]),
    })
    ```
    """

    def __init__(
        self,
        schema: GraphQLSchema,
        graphiql: bool = True,
    ):
        self.schema = schema
        self.graphiql = graphiql
        super().__init__()

    # def headers(self):
    #     return {
    #         header_name.decode("utf-8").lower(): header_value.decode("utf-8")
    #         for header_name, header_value in self.scope["headers"]
    #     }

    # async def parse_multipart_body(self, body):
    #     await self.send_response(500, "Unable to parse the multipart body")
    #     return None

    # async def get_graphql_params(self, data):
    #     query = data.get("query")
    #     variables = data.get("variables")
    #     id = data.get("id")

    #     if variables and isinstance(variables, str):
    #         try:
    #             variables = json.loads(variables)
    #         except Exception:
    #             await self.send_response(500, b"Variables are invalid JSON.")
    #             return None
    #     operation_name = data.get("operationName")

    #     return query, variables, operation_name, id

    # async def get_request_data(self, body) -> Optional[Any]:
    #     if self.headers.get("content-type", "").startswith("multipart/form-data"):
    #         data = await self.parse_multipart_body(body)
    #         if data is None:
    #             return None
    #     else:
    #         try:
    #             data = json.loads(body)
    #         except json.JSONDecodeError:
    #             await self.send_response(500, b"Unable to parse request body as JSON")
    #             return None

    #     query, variables, operation_name, id = self.get_graphql_params(data)
    #     if not query:
    #         await self.send_response(500, b"No GraphQL query found in the request")
    #         return None

    #     return query, variables, operation_name, id

    # async def post(self, body):
    #     request_data = await self.get_request_data(body)
    #     if request_data is None:
    #         return
    #     context = await self.get_context()
    #     root_value = await self.get_root_value()

    #     result = await self.schema.execute(
    #         query=request_data.query,
    #         root_value=root_value,
    #         variable_values=request_data.variables,
    #         context_value=context,
    #         operation_name=request_data.operation_name,
    #     )

    #     response_data = self.process_result(result)
    #     await self.send_response(
    #         200,
    #         json.dumps(response_data).encode("utf-8"),
    #         headers=[(b"Content-Type", b"application/json")],
    #     )

    # def graphiql_html_file_path(self) -> Path:
    #     return Path(__file__).parent.parent.parent / "static" / "graphiql.html"

    # async def render_graphiql(self, body):
    #     html_string = self.graphiql_html_file_path.read_text()
    #     html_string = html_string.replace("{{ SUBSCRIPTION_ENABLED }}", "true")
    #     await self.send_response(
    #         200, html_string.encode("utf-8"), headers=[(b"Content-Type", b"text/html")]
    #     )

    # def should_render_graphiql(self):
    #     return bool(self.graphiql and "text/html" in self.headers.get("accept", ""))

    # async def get(self, body):
    #     # if self.should_render_graphiql():
    #     #     return await self.render_graphiql(body)
    #     # else:
    #     await self.send_response(
    #         200, "{}", headers=[(b"Content-Type", b"text/json")]
    #     )

    async def handle(self, body):
        # if self.scope["method"] == "GET":
        #     return await self.get(body)
        # if self.scope["method"] == "POST":
        #     return await self.post(body)
        await self.send_response(
            200, b"Method not allowed", headers=[b"Allow", b"GET, POST"]
        )

    # async def get_root_value(self) -> Any:
    #     return None

    # async def get_context(self) -> Any:
    #     return None

    # def process_result(self, result: ExecutionResult):
    #     return result.formatted
