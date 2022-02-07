async def render_graphiql_async(
    data: GraphiQLData,
    config: GraphiQLConfig,
    options: Optional[GraphiQLOptions] = None,
) -> str:
    graphiql_template, template_vars = _render_graphiql(data, config, options)
    jinja_env: Optional[Environment] = config.get("jinja_env")

    if jinja_env:
        # This method returns a Template. See https://jinja.palletsprojects.com/en/2.11.x/api/#jinja2.Template
        template = jinja_env.from_string(graphiql_template)
        if jinja_env.is_async:  # type: ignore
            source = await template.render_async(**template_vars)
        else:
            source = template.render(**template_vars)
    else:
        source = simple_renderer(graphiql_template, **template_vars)
    return source
