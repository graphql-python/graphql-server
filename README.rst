GraphQL-Server-Core
===================

|Build Status| |Coverage Status| |PyPI version|

GraphQL-Server-Core is a base library that serves as a helper for
building GraphQL servers or integrations into existing web frameworks
using `GraphQL-Core <https://github.com/graphql-python/graphql-core>`__.

Existing integrations built with GraphQL-Server-Core
----------------------------------------------------

=========================== ==========================================================================================================
Server integration          Package
=========================== ==========================================================================================================
Flask                       `flask-graphql <https://github.com/graphql-python/flask-graphql/>`__
Sanic                       `sanic-graphql <https://github.com/graphql-python/sanic-graphql/>`__
AIOHTTP                     `aiohttp-graphql <https://github.com/graphql-python/aiohttp-graphql>`__
WebOb (Pyramid, TurboGears) `webob-graphql <https://github.com/graphql-python/webob-graphql/>`__
WSGI                        `wsgi-graphql <https://github.com/moritzmhmk/wsgi-graphql>`__
Responder                   `responder.ext.graphql <https://github.com/kennethreitz/responder/blob/master/responder/ext/graphql.py>`__
=========================== ==========================================================================================================

Other integrations using GraphQL-Core or Graphene
-------------------------------------------------

================== ========================================================================
Server integration Package
================== ========================================================================
Django             `graphene-django <https://github.com/graphql-python/graphene-django/>`__
================== ========================================================================

Documentation
-------------

The ``graphql_server`` package provides these three public helper
functions:

-  ``run_http_query``
-  ``encode_execution_results``
-  ``laod_json_body``

All functions in the package are annotated with type hints and
docstrings, and you can build HTML documentation from these using
``bin/build_docs``.

You can also use one of the existing integrations listed above as
blueprint to build your own integration or GraphQL server
implementations.

Please let us know when you have built something new, so we can list it
here.

.. |Build Status| image:: https://travis-ci.org/graphql-python/graphql-server-core.svg?branch=master
   :target: https://travis-ci.org/graphql-python/graphql-server-core
.. |Coverage Status| image:: https://coveralls.io/repos/graphql-python/graphql-server-core/badge.svg?branch=master&service=github
   :target: https://coveralls.io/github/graphql-python/graphql-server-core?branch=master
.. |PyPI version| image:: https://badge.fury.io/py/graphql-server-core.svg
   :target: https://badge.fury.io/py/graphql-server-core
