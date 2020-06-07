import json

_slash_escape = "\\/" not in json.dumps("/")


def dumps(obj, **kwargs):
    """Serialize ``obj`` to a JSON formatted ``str`` by using the application's
    configured encoder (:attr:`~webob.WebOb.json_encoder`) if there is an
    application on the stack.
    This function can return ``unicode`` strings or ascii-only bytestrings by
    default which coerce into unicode strings automatically.  That behavior by
    default is controlled by the ``JSON_AS_ASCII`` configuration variable
    and can be overridden by the simplejson ``ensure_ascii`` parameter.
    """
    encoding = kwargs.pop("encoding", None)
    rv = json.dumps(obj, **kwargs)
    if encoding is not None and isinstance(rv, str):
        rv = rv.encode(encoding)
    return rv


def htmlsafe_dumps(obj, **kwargs):
    """Works exactly like :func:`dumps` but is safe for use in ``<script>``
    tags.  It accepts the same arguments and returns a JSON string.  Note that
    this is available in templates through the ``|tojson`` filter which will
    also mark the result as safe.  Due to how this function escapes certain
    characters this is safe even if used outside of ``<script>`` tags.
    The following characters are escaped in strings:
    -   ``<``
    -   ``>``
    -   ``&``
    -   ``'``
    This makes it safe to embed such strings in any place in HTML with the
    notable exception of double quoted attributes.  In that case single
    quote your attributes or HTML escape it in addition.
    .. versionchanged:: 0.10
       This function's return value is now always safe for HTML usage, even
       if outside of script tags or if used in XHTML.  This rule does not
       hold true when using this function in HTML attributes that are double
       quoted.  Always single quote attributes if you use the ``|tojson``
       filter.  Alternatively use ``|tojson|forceescape``.
    """
    rv = (
        dumps(obj, **kwargs)
        .replace(u"<", u"\\u003c")
        .replace(u">", u"\\u003e")
        .replace(u"&", u"\\u0026")
        .replace(u"'", u"\\u0027")
    )
    if not _slash_escape:
        rv = rv.replace("\\/", "/")
    return rv


def tojson(obj, **kwargs):
    return htmlsafe_dumps(obj, **kwargs)
