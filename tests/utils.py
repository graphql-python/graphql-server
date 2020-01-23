def as_dicts(results):
    """Convert execution results to a list of tuples of dicts for better comparison."""
    return [result.to_dict(dict_class=dict) for result in results]
