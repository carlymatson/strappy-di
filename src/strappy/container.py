"""Container for dependency injection."""

import inspect
from collections.abc import Callable, Hashable
from enum import Enum
from typing import Any, Self, TypeAlias, TypeVar, overload

from strappy import strategies
from strappy.errors import RegistrationConflictError, ResolutionError
from strappy.protocols import ContainerLike, FactoryDecorator
from strappy.provider import Provider, Scope

T = TypeVar("T")
Factory: TypeAlias = type[T] | Callable[..., T]
FactoryT = TypeVar("FactoryT", bound=Factory)


class Mode(Enum):
    """Mode for resolving multiple registrations for the same provides."""

    RAISE_ON_CONFLICT = "RAISE_ON_CONFLICT"
    OVERWRITE = "OVERWRITE"
    APPEND = "APPEND"


class _Empty: ...


_EMPTY = _Empty()


class Container:
    """Simple dependency injection container."""

    def __init__(
        self,
        custom_resolvers: list[Callable[[inspect.Parameter, ContainerLike], Provider]]
        | None = None,
        parent: Self | None = None,
    ) -> None:
        """Create a new  container for dependency injection."""
        self.custom_resolvers = custom_resolvers or []
        self.parent = parent

        self._registry: dict[Hashable, list[Provider]] = {}
        self._default_resolvers = [
            strategies.search_annotations_and_default_for_depends,
            strategies.search_for_subtypes,
            strategies.search_for_collection_inner_type,
        ]

    def unset(self, key: Hashable) -> None:
        """Clear all registrations for the given type."""
        self._registry.pop(key, None)

    def clear(self, key: Hashable) -> None:
        """Clear all registrations for the given type."""
        self._registry[key] = []

    def _add_one(
        self,
        provider: Provider,
        mode: Mode = Mode.RAISE_ON_CONFLICT,
    ) -> None:
        """Add a provider to the container registry."""
        if mode == Mode.RAISE_ON_CONFLICT and provider.provides in self._registry:
            raise RegistrationConflictError(str(provider.provides))
        if mode == Mode.OVERWRITE:
            self.clear(provider.provides)
        self._registry.setdefault(provider.provides, [])
        self._registry[provider.provides].append(provider)

    def add(
        self,
        *providers: Provider,
        mode: Mode = Mode.RAISE_ON_CONFLICT,
    ) -> None:
        """Add a provider to the container registry."""
        if mode == Mode.RAISE_ON_CONFLICT:
            seen = set(self._registry)
            for provider in providers:
                if provider.provides in seen:
                    raise RegistrationConflictError(str(provider.provides))
                seen.add(provider.provides)

        for provider in providers:
            self._add_one(provider, mode=mode)

    @property
    def registry(self) -> dict[Hashable, list[Provider]]:
        """Get the combined registry from this container and its ancestors."""
        if self.parent:
            return {**self.parent.registry, **self._registry}
        return {**self._registry}

    @overload
    def inject(
        self,
        factory: type[T],
        *,
        provides: None = None,
        kwargs: None = None,
        scope: None = None,
        mode: Mode = Mode.RAISE_ON_CONFLICT,
    ) -> type[T]: ...

    @overload
    def inject(
        self,
        factory: Callable[..., T],
        *,
        provides: None = None,
        kwargs: None = None,
        scope: None = None,
        mode: Mode = Mode.RAISE_ON_CONFLICT,
    ) -> Callable[..., T]: ...

    @overload
    def inject(
        self,
        factory: None = None,
        *,
        provides: Callable[..., T] | None = None,
        kwargs: dict[str, Any] | None = None,
        scope: Scope | None = None,
        mode: Mode = Mode.RAISE_ON_CONFLICT,
    ) -> FactoryDecorator[T]: ...

    def inject(
        self,
        factory: Callable[..., T] | None = None,
        *,
        provides: Callable[..., T] | None = None,
        kwargs: dict[str, Any] | None = None,
        scope: Scope | None = None,
        mode: Mode = Mode.RAISE_ON_CONFLICT,
    ) -> type[T] | Callable[..., T] | FactoryDecorator[T]:
        """Inject a factory into this container."""
        # Case 1: Decorator without arguments, i.e. @inject
        if factory is not None:
            self.add(Provider(factory=factory))
            return factory

        # Case 2: Decorator with arguments, i.e. @inject(...)
        def decorator(factory_: FactoryT) -> FactoryT:
            self.add(
                Provider(
                    factory=factory_,
                    kwargs=kwargs,
                    scope=scope,
                    provides=provides,
                ),
                mode=mode,
            )
            return factory_

        return decorator

    def _resolve_param(
        self,
        param: inspect.Parameter,
        args: tuple = (),
        kwargs: dict[str, Any] | None = None,
    ) -> Any:  # noqa: ANN401
        type_resolvers = self.custom_resolvers + self._default_resolvers
        providers = [
            result
            for strategy in type_resolvers
            if (result := strategy(param, self)) is not None
        ]
        if providers:
            return providers[0].get(self, kwargs=kwargs)
        return _EMPTY

    def resolve(
        self,
        service: type[T],
        args: tuple = (),
        kwargs: dict[str, Any] | None = None,
    ) -> T:
        """Get an instance from the container's registered providers."""
        result = self._resolve_param(
            inspect.Parameter(  # name and kind are arbitrary
                name="_",
                kind=inspect._ParameterKind.POSITIONAL_ONLY,  # noqa: SLF001
                annotation=service,
            ),
            args=args,
            kwargs=kwargs,
        )
        if result is not _EMPTY:
            return result
        raise ResolutionError

    def call(
        self,
        function: Callable[..., T],
        *,
        kwargs: dict[str, Any] | None = None,
    ) -> T:
        """Call a callable within the container's context."""
        provided_kwargs = kwargs or {}
        skip = {"self", "cls"}.union(provided_kwargs)
        params = inspect.signature(function).parameters
        resolved_kwargs = {
            key: resolved
            for key, param in params.items()
            if key not in skip
            and (resolved := self._resolve_param(param)) is not _EMPTY
        }
        build_kwargs = {**resolved_kwargs, **provided_kwargs}
        positional_args = tuple(
            build_kwargs.pop(name)
            for name, param in params.items()
            if param.kind == inspect._ParameterKind.POSITIONAL_ONLY  # noqa: SLF001
        )
        return function(*positional_args, **build_kwargs)

    def extend(self) -> Self:
        """Return a new container extending the current context."""
        return type(self)(custom_resolvers=self.custom_resolvers, parent=self)
