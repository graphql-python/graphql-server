"""Based on (express-graphql)[https://github.com/graphql/express-graphql/blob/master/src/renderGraphiQL.js] and
(subscriptions-transport-ws)[https://github.com/apollographql/subscriptions-transport-ws]"""
import json
import re
from typing import Any, Dict, Optional, Tuple
from graphql_server import GraphQLParams

from typing_extensions import TypedDict

GRAPHIQL_VERSION = "1.0.3"

GRAPHIQL_TEMPLATE = """<!--
The request to this GraphQL server provided the header "Accept: text/html"
and as a result has been presented GraphiQL - an in-browser IDE for
exploring GraphQL.
If you wish to receive JSON, provide the header "Accept: application/json" or
add "&raw" to the end of the URL within a browser.
-->
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>{{html_title}}</title>
  <meta name="robots" content="noindex" />
  <meta name="referrer" content="origin" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body {
      margin: 0;
      overflow: hidden;
    }
    #graphiql {
      height: 100vh;
    }
  </style>
  <link href="//cdn.jsdelivr.net/npm/graphiql@{{graphiql_version}}/graphiql.css" rel="stylesheet" />
  <script src="//cdn.jsdelivr.net/npm/promise-polyfill@8.1.3/dist/polyfill.min.js"></script>
  <script src="//cdn.jsdelivr.net/npm/unfetch@4.1.0/dist/unfetch.umd.js"></script>
  <script src="//cdn.jsdelivr.net/npm/react@16.13.1/umd/react.production.min.js"></script>
  <script src="//cdn.jsdelivr.net/npm/react-dom@16.13.1/umd/react-dom.production.min.js"></script>
  <script src="//cdn.jsdelivr.net/npm/graphiql@{{graphiql_version}}/graphiql.min.js"></script>
  <script src="//cdn.jsdelivr.net/npm/subscriptions-transport-ws@0.9.16/browser/client.js"></script>
  <script src="//cdn.jsdelivr.net/npm/graphiql-subscriptions-fetcher@0.0.2/browser/client.js"></script>
</head>
<body>
  <div id="graphiql">Loading...</div>
  <script>
    // Collect the URL parameters
    var parameters = {};
    window.location.search.substr(1).split('&').forEach(function (entry) {
      var eq = entry.indexOf('=');
      if (eq >= 0) {
        parameters[decodeURIComponent(entry.slice(0, eq))] =
          decodeURIComponent(entry.slice(eq + 1));
      }
    });
    // Produce a Location query string from a parameter object.
    function locationQuery(params) {
      return '?' + Object.keys(params).filter(function (key) {
        return Boolean(params[key]);
      }).map(function (key) {
        return encodeURIComponent(key) + '=' +
          encodeURIComponent(params[key]);
      }).join('&');
    }
    // Derive a fetch URL from the current URL, sans the GraphQL parameters.
    var graphqlParamNames = {
      query: true,
      variables: true,
      operationName: true
    };
    var otherParams = {};
    for (var k in parameters) {
      if (parameters.hasOwnProperty(k) && graphqlParamNames[k] !== true) {
        otherParams[k] = parameters[k];
      }
    }
    // Configure the subscription client
    let subscriptionsFetcher = null;
    let subscriptionUrl = {{subscription_url}};
    if (subscriptionUrl) {
      let subscriptionsClient = new SubscriptionsTransportWs.SubscriptionClient(
        subscriptionUrl,
        { reconnect: true }
      );
      subscriptionsFetcher = GraphiQLSubscriptionsFetcher.graphQLFetcher(
        subscriptionsClient,
        graphQLFetcher
      );
    }
    var fetchURL = locationQuery(otherParams);
    // Defines a GraphQL fetcher using the fetch API.
    function graphQLFetcher(graphQLParams, opts) {
      return fetch(fetchURL, {
        method: 'post',
        headers: Object.assign(
          {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          },
          opts && opts.headers,
        ),
        body: JSON.stringify(graphQLParams),
        credentials: 'include',
      }).then(function (response) {
        return response.json();
      });
    }
    // When the query and variables string is edited, update the URL bar so
    // that it can be easily shared.
    function onEditQuery(newQuery) {
      parameters.query = newQuery;
      updateURL();
    }
    function onEditVariables(newVariables) {
      parameters.variables = newVariables;
      updateURL();
    }
    function onEditHeaders(newHeaders) {
      parameters.headers = newHeaders;
      updateURL();
    }
    function onEditOperationName(newOperationName) {
      parameters.operationName = newOperationName;
      updateURL();
    }
    function updateURL() {
      history.replaceState(null, null, locationQuery(parameters));
    }
    // Render <GraphiQL /> into the body.
    ReactDOM.render(
      React.createElement(GraphiQL, {
        fetcher: subscriptionsFetcher || graphQLFetcher,
        onEditQuery: onEditQuery,
        onEditVariables: onEditVariables,
        onEditHeaders: onEditHeaders,
        onEditOperationName: onEditOperationName,
        query: {{query}},
        response: {{result}},
        variables: {{variables}},
        headers: {{headers}},
        operationName: {{operation_name}},
        defaultQuery: {{default_query}},
        headerEditorEnabled: {{header_editor_enabled}},
        shouldPersistHeaders: {{should_persist_headers}}
      }),
      document.getElementById('graphiql')
    );
  </script>
</body>
</html>"""


class GraphiQLOptions(TypedDict):
    """GraphiQL options to display on the UI.

    Has the following attributes:

    graphiql_version
        The version of the provided GraphiQL package.
    graphiql_html_title
        Replace the default html title on the GraphiQL.
    default_query
        An optional GraphQL string to use when no query is provided and no stored
        query exists from a previous session. If None is provided, GraphiQL
        will use its own default query.
    header_editor_enabled
        An optional boolean which enables the header editor when true.
        Defaults to false.
    should_persist_headers
        An optional boolean which enables to persist headers to storage when true.
        Defaults to false.
    subscription_url
        The GraphiQL socket endpoint for using subscriptions in graphql-ws.
    headers
        An optional GraphQL string to use as the initial displayed request headers,
        if None is provided, the stored headers will be used.
    """

    html_title: Optional[str]
    graphiql_version: Optional[str]
    default_query: Optional[str]
    header_editor_enabled: Optional[bool]
    should_persist_headers: Optional[bool]
    subscription_url: Optional[str]
    headers: Optional[str]


GRAPHIQL_DEFAULT_OPTIONS: GraphiQLOptions = {
    "html_title": "GraphiQL",
    "graphiql_version": GRAPHIQL_VERSION,
    "default_query": "",
    "header_editor_enabled": True,
    "should_persist_headers": False,
    "subscription_url": None,
    "headers": "",
}


def escape_js_value(value: Any) -> Any:
    quotation = False
    if value.startswith('"') and value.endswith('"'):
        quotation = True
        value = value[1 : len(value) - 1]

    value = value.replace("\\\\n", "\\\\\\n").replace("\\n", "\\\\n")
    if quotation:
        value = '"' + value.replace('\\\\"', '"').replace('"', '\\"') + '"'

    return value


def tojson(value):
    if value not in ["true", "false", "null", "undefined"]:
        value = json.dumps(value)
        # value = escape_js_value(value)
    return value


def simple_renderer(template: str, **values: Dict[str, Any]) -> str:
    def get_var(match_obj):
        var_name = match_obj.group(1)
        if var_name is not None:
            return values[var_name]
        return ""

    pattern = r"{{\s*([^}]+)\s*}}"

    return re.sub(pattern, get_var, template)


def get_template_vars(
    data: str,
    params: GraphQLParams,
    options: Optional[GraphiQLOptions] = None,
) -> Tuple[str, Dict[str, Any]]:
    """When render_graphiql receives a request which does not Accept JSON, but does
    Accept HTML, it may present GraphiQL, the in-browser GraphQL explorer IDE.
    When shown, it will be pre-populated with the result of having executed
    the requested query.
    """
    options_with_defaults = dict(GRAPHIQL_DEFAULT_OPTIONS, **(options or {}))

    template_vars: Dict[str, Any] = {
        "result": tojson(data),
        "query": tojson(params.query),
        "variables": tojson(json.dumps(params.variables)),
        "operation_name": tojson(params.operation_name),
        "html_title": options_with_defaults["html_title"],
        "graphiql_version": options_with_defaults["graphiql_version"],
        "subscription_url": tojson(options_with_defaults["subscription_url"]),
        "headers": tojson(options_with_defaults["headers"]),
        "default_query": tojson(options_with_defaults["default_query"]),
        "header_editor_enabled": tojson(options_with_defaults["header_editor_enabled"]),
        "should_persist_headers": tojson(
            options_with_defaults["should_persist_headers"]
        ),
    }

    return template_vars


def render_graphiql_sync(
    result: str,
    params: GraphQLParams,
    options: Optional[GraphiQLOptions] = None,
) -> str:
    template_vars = get_template_vars(result, params, options)
    source = simple_renderer(GRAPHIQL_TEMPLATE, **template_vars)
    return source
