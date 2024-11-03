"""Shared generic types and protocols."""

from collections.abc import Callable, Hashable
from typing import Any, Protocol, TypeAlias, TypeVar

T = TypeVar("T")
Factory: TypeAlias = type[T] | Callable[..., T]
FactoryT = TypeVar("FactoryT", bound=type | Callable)


class ContainerLike(Protocol):
    """Protocol describing an object that can resolve needs for parameters."""

    @property
    def registry(self) -> dict[Hashable, list]:
        """Property for getting dictionary of registered providers."""
        ...

    def call(
        self,
        function: Callable[..., T],
        *,
        kwargs: dict[str, Any] | None = None,
    ) -> T:
        """Call a function or class by recursively resolving dependencies."""
        ...
