from flask import Flask

from graphql_server.flask import GraphQLView
from tests.flask.schema import Schema


def create_app(path="/graphql", schema=Schema, **kwargs):
    server = Flask(__name__)
    server.debug = True
    view_cls = GraphQLView
    server.add_url_rule(
        path,
        view_func=view_cls.as_view("graphql", schema=schema, **kwargs),
    )
    return server


if __name__ == "__main__":
    app = create_app(graphiql=True)
    app.run()
