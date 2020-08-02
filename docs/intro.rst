Introduction
============

`GraphQL-Server`_ is a base library that serves as a helper for building GraphQL
servers or integrations into existing web frameworks using `GraphQL-Core-3`_.

The package also provides some built-in server integrations:

- Flask
- WebOb
- Sanic
- AIOHTTP

Any other existing server frameworks can be implemented by using the public
helper functions provided on this package.

Getting started
---------------

You can install GraphQL-Server using pip_::

    pip install graphql-server

You can also install GraphQL-Server with pipenv_, if you prefer that::

    pipenv install graphql-server

Now you can start using GraphQL-Server by importing from the top-level
:mod:`graphql-server` package. Nearly everything defined in the sub-packages
can also be imported directly from the top-level package.

.. currentmodule:: graphql_server

Using the public helper functions, you can define a GraphQLView class on your
server and start adding the graphiql options along with parsing, validation and
execution functions related to graphql.


Reporting Issues and Contributing
---------------------------------

Please visit the `GitHub repository of GraphQL-Server`_ if you're interested
in the current development or want to report issues or send pull requests.

.. _GraphQL-Core-3: https://github.com/graphql-python/graphql-core
.. _GraphQL-Server: https://github.com/graphql-python/graphql-server
.. _GitHub repository of GraphQL-Server: https://github.com/graphql-python/graphql-server
.. _pip: https://pip.pypa.io/
.. _pipenv: https://github.com/pypa/pipenv