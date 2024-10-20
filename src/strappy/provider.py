"""Dependency providers."""

import inspect
from collections.abc import Callable, Hashable
from enum import Enum
from typing import Any, Generic, TypeVar

from strappy.errors import (
    MultipleImplementationsError,
    NoImplementationError,
    NoProviderTypeError,
    ResolutionError,
    TransientInstanceError,
)
from strappy.protocols import ContainerLike

T = TypeVar("T")


class Scope(Enum):
    """Scope of a provider."""

    TRANSIENT = "TRANSIENT"
    SINGLETON = "SINGLETON"


class Provider(Generic[T]):
    """Object used to get an instance that implements a type."""

    _type_arg = None

    def __init__(
        self,
        factory: Callable[..., T] | None = None,
        *,
        instance: T | None = None,
        kwargs: dict[str, Any] | None = None,
        scope: Scope | None = None,
        provides: type[T] | Callable[..., T] | None = None,
    ) -> None:
        """Instantiate a new provider."""
        self.factory = factory
        self.instance = instance
        self.registration_kwargs = kwargs
        self.scope = scope or Scope.TRANSIENT
        self.provides = provides or self._get_type()
        self._result = None

        if self.instance is not None:
            self._result = self.instance
            self.scope = scope or Scope.SINGLETON

        self._validate()

    def __class_getitem__(cls, key: Hashable) -> "type[Provider]":
        """Set the type argument of parametrized generic."""

        class Provider(cls):
            _type_arg = key

        return Provider

    def _get_type(self) -> Any:  # noqa: ANN401
        if getattr(self, "provides", None):
            return self.provides
        if self._type_arg:
            return self._type_arg
        if isinstance(self.factory, type):
            return self.factory
        if self.factory is not None:
            return_annotation = inspect.signature(self.factory).return_annotation
            if return_annotation is inspect._empty:  # noqa: SLF001
                raise NoProviderTypeError
            return return_annotation
        return type(self.instance)

    def _validate(self) -> None:
        if self.factory is None and self.instance is None:
            raise NoImplementationError
        if self.factory is not None and self.instance is not None:
            raise MultipleImplementationsError
        if self.instance is not None and self.scope == Scope.TRANSIENT:
            raise TransientInstanceError

    def _build(
        self,
        resolver: ContainerLike,
        args: tuple = (),  # noqa: ARG002
        kwargs: dict[str, Any] | None = None,
    ) -> T:
        if self.instance is not None:
            return self.instance
        if self.factory:
            build_kwargs = {
                **(self.registration_kwargs or {}),
                **(kwargs or {}),
            }
            try:
                result = resolver.call(self.factory, kwargs=build_kwargs)
            except TypeError as exc:
                raise ResolutionError from exc
            return result
        raise NoImplementationError

    def get(
        self,
        resolver: ContainerLike,
        args: tuple = (),
        kwargs: dict[str, Any] | None = None,
    ) -> T:
        """Get result from provider."""
        if self.scope == Scope.SINGLETON:
            if self._result is not None:
                return self._result
            if kwargs:
                # Resolution kwargs are silently ignored for singletons
                kwargs = None
        result = self._build(resolver, args=args, kwargs=kwargs)
        if self.scope == Scope.SINGLETON:
            self._result = result
        return result
