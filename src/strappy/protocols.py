"""Shared protocol."""

from collections.abc import Callable, Hashable
from typing import Any, Generic, Protocol, TypeVar, overload

T = TypeVar("T")


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


class FactoryDecorator(Protocol, Generic[T]):
    """Protocol description of a decorator."""

    @overload
    def __call__(self, factory_: type[T]) -> type[T]: ...
    @overload
    def __call__(self, factory_: Callable[..., T]) -> Callable[..., T]: ...
    def __call__(  # noqa: D102
        self,
        factory_: type[T] | Callable[..., T],
    ) -> type[T] | Callable[..., T]: ...
