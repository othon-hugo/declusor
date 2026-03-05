from string import Template


def format_client_script(client_script: str, /, **kwargs: str | int) -> str:
    """Read a client script from the default clients directory, substitute variables, and format it for use.

    Args:
        client_script: The client script.
        **kwargs: Key-value pairs to substitute into the client script template.

    Returns:
        The formatted client script with variables substituted.
    """

    return Template(client_script).safe_substitute(**kwargs)
