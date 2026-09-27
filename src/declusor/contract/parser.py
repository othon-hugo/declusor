from typing import Any, Protocol, TypedDict, runtime_checkable


class ParsedArguments(TypedDict):
    """Base TypedDict for plugin-specific parsed options.

    Autonomous plugins subclass this to declare their statically typed options.
    Parsers never construct this directly — plugins do via ``extract_options()``.
    """


@runtime_checkable
class IArgumentParser(Protocol):
    """Protocol for an argument parser that registers command-line arguments.

    Matches ``argparse.ArgumentParser``, ``util.Parser``, and ``DeclusorParser``
    structurally without multiple-inheritance conflicts.
    """

    def add_argument(self, *name_or_flags: str, **kwargs: Any) -> object:
        """Register a command-line argument or option.

        Args:
            *name_or_flags: One positional name or one or more option flags
                (e.g. ``\"host\"`` or ``\"-p\"``, ``\"--plugin\"``).
            **kwargs: Forwarded verbatim to the underlying parser implementation
                (e.g. ``type``, ``default``, ``help``, ``nargs``).
        """
        ...
