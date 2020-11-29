.. _flask:

Flask
-----

In order to add GraphQL support to your Flask application, run the below command
on your terminal::

    pip install graphql-server[flask]

Now you must use the *GraphQLView* view from *graphql_server.flask* in order to
add the ``/graphql`` endpoint to your app and enable the GraphiQL IDE.

Example:

.. literalinclude:: ../code_examples/flask_server.py


.. note::
    If you are using the `Schema` type of `Graphene`_ library, be sure to use
    the *graphql_schema* attribute from the schema instance to pass as schema on
    the *GraphQLView* view. Otherwise, the *GraphQLSchema* from *graphql-core*
    is the way to go.

    More info at `Graphene v3 release notes`_ and `GraphQL-core 3 usage`_.


Supported options for GraphQLView
=================================

The GraphiQL itself supports several options based on the official
implementation:

    * **schema**: The ``GraphQLSchema`` object that you want the view to execute when it gets a valid request.
    * **context**: A value to pass as the ``context_value`` to graphql ``execute`` function.
      By default is set to ``dict`` with request object at key ``request``.
    * **root_value**: The ``root_value`` you want to provide to graphql ``execute``.
    * **pretty**: Whether or not you want the response to be pretty printed JSON.
    * **graphiql**: If **True**, may present `GraphiQL`_ when loaded directly from the browser
      (a useful tool for debugging and exploration).
    * **graphiql_version**: The graphiql version to load. Defaults to **"1.0.3"**.
    * **graphiql_template**: Inject a Jinja template string to customize GraphiQL.
    * **graphiql_html_title**: The graphiql title to display. Defaults to **"GraphiQL"**.
    * **batch**: Set the GraphQL view as batch (for using in `Apollo-Client`_ or `ReactRelayNetworkLayer`_)
    * **middleware**: A list of graphql `middlewares`_.
    * **encode**: the encoder to use for responses (sensibly defaults to ``graphql_server.json_encode``).
    * **format_error**: the error formatter to use for responses (sensibly defaults to ``graphql_server.default_format_error``.
    * **subscriptions**: The GraphiQL socket endpoint for using subscriptions in `graphql-ws`_.
    * **headers**: An optional GraphQL string to use as the initial displayed request headers, if not provided, 
      the stored headers will be used.
    * **default_query**: An optional GraphQL string to use when no query is provided and no stored query 
      exists from a previous session.
      If not provided, GraphiQL will use its own default query.
    * **header_editor_enabled**: An optional boolean which enables the header editor when true.
      Defaults to **false**.
    * **should_persist_headers**:  An optional boolean which enables to persist headers to storage when true.
      Defaults to **false**.


You can also subclass *GraphQLView* and overwrite *get_root_value(self,
request)* to have a dynamic root value per request.

.. code-block:: python

    class UserRootValue(GraphQLView):
        def get_root_value(self, request):
            return request.user



.. _Graphene: https://github.com/graphql-python/graphene
.. _Graphene v3 release notes: https://github.com/graphql-python/graphene/wiki/v3-release-notes#graphene-schema-no-longer-subclasses-graphqlschema-type
.. _GraphQL-core 3 usage: https://github.com/graphql-python/graphql-core#usage
.. _GraphiQL: https://github.com/graphql/graphiql
.. _ReactRelayNetworkLayer: https://github.com/nodkz/react-relay-network-layer
.. _Apollo-Client: http://dev.apollodata.com/core/network.html#query-batching
.. _middlewares: http://docs.graphene-python.org/en/latest/execution/middleware/
.. _graphql-ws: https://github.com/graphql-python/graphql-ws