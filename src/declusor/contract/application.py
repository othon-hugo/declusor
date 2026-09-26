from collections.abc import Callable, Sequence
from pathlib import Path

from declusor import core

ApplicationFactory = Callable[[Sequence[Path] | None], core.ApplicationProtocol]
