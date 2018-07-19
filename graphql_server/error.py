class HttpQueryError(Exception):
    def __init__(self, status_code, message=None, is_graphql_error=False, headers=None):
        self.status_code = status_code
        self.message = message
        self.is_graphql_error = is_graphql_error
        self.headers = headers
        super(HttpQueryError, self).__init__(message)

    def __eq__(self, other):
        return (
            isinstance(other, HttpQueryError)
            and other.status_code == self.status_code
            and other.message == self.message
            and other.headers == self.headers
        )

    def __hash__(self):
        if self.headers:
            headers_hash = tuple(self.headers.items())
        else:
            headers_hash = None

        return hash((self.status_code, self.message, headers_hash))
