from graphql_server import HttpQueryError


def test_create_http_query_error():

    error = HttpQueryError(420, "Some message", headers={"SomeHeader": "SomeValue"})
    assert error.status_code == 420
    assert error.message == "Some message"
    assert error.headers == {"SomeHeader": "SomeValue"}


def test_compare_http_query_errors():

    error = HttpQueryError(400, "Message", headers={"Header": "Value"})
    assert error == HttpQueryError(400, "Message", headers={"Header": "Value"})
    assert error != HttpQueryError(420, "Message", headers={"Header": "Value"})
    assert error != HttpQueryError(400, "Other Message", headers={"Header": "Value"})
    assert error != HttpQueryError(400, "Message", headers={"Header": "OtherValue"})


def test_hash_http_query_errors():

    error = HttpQueryError(400, "Foo", headers={"Bar": "Baz"})

    assert hash(error) == hash(HttpQueryError(400, "Foo", headers={"Bar": "Baz"}))
    assert hash(error) != hash(HttpQueryError(420, "Foo", headers={"Bar": "Baz"}))
    assert hash(error) != hash(HttpQueryError(400, "Boo", headers={"Bar": "Baz"}))
    assert hash(error) != hash(HttpQueryError(400, "Foo", headers={"Bar": "Faz"}))
