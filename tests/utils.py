from typing import List

from graphql import ExecutionResult


def as_dicts(results: List[ExecutionResult]):
    """Convert execution results to a list of tuples of dicts for better comparison."""
    return [
        {
            "data": result.data,
            "errors": [error.formatted for error in result.errors]
            if result.errors
            else result.errors,
        }
        for result in results
    ]
