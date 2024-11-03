"""Container for dependency injection."""

import inspect
from collections.abc import Callable, Hashable, Mapping, Sequence
from enum import Enum
from typing import Any, TypeAlias, overload

from typing_extensions import Self

from strappy import strategies as st
from strappy.errors import RegistrationConflictError, ResolutionError
from strappy.provider import Provider, Scope
from strappy.types import ContainerLike, FactoryT, T

Decorator: TypeAlias = Callable[[FactoryT], FactoryT]
Strategy: TypeAlias = Callable[[inspect.Parameter, ContainerLike], Provider | None]


class RegisterMode(Enum):
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
        strategies: Sequence[Strategy] = (
            st.use_depends_meta_if_present,
            st.search_registry_for_type,
            st.search_registry_for_collection_inner_type,
            st.use_type_as_factory,
        ),
        parent: Self | None = None,
    ) -> None:
        """Create a new  container for dependency injection."""
        self.strategies = strategies or []
        self.parent = parent

        self._registry: dict[Hashable, list[Provider]] = {}

    def unset(self, key: Hashable) -> None:
        """Clear all registrations for the given type."""
        self._registry.pop(key, None)

    def clear(self, key: Hashable) -> None:
        """Clear all registrations for the given type."""
        self._registry[key] = []

    def _add_one(
        self,
        provider: Provider,
        mode: RegisterMode = RegisterMode.RAISE_ON_CONFLICT,
    ) -> None:
        """Add a provider to the container registry."""
        if (
            mode == RegisterMode.RAISE_ON_CONFLICT
            and provider.provides in self._registry
        ):
            raise RegistrationConflictError(str(provider.provides))
        if mode == RegisterMode.OVERWRITE:
            self.clear(provider.provides)
        self._registry.setdefault(provider.provides, [])
        self._registry[provider.provides].append(provider)

    def add(
        self,
        *providers: Provider,
        mode: RegisterMode = RegisterMode.RAISE_ON_CONFLICT,
    ) -> None:
        """Add a provider to the container registry."""
        if mode == RegisterMode.RAISE_ON_CONFLICT:
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
    def register(
        self,
        factory: FactoryT,
        *,
        provides: None = None,
        kwargs: None = None,
        scope: None = None,
        mode: RegisterMode = RegisterMode.RAISE_ON_CONFLICT,
    ) -> FactoryT: ...

    @overload
    def register(
        self,
        factory: None = None,
        *,
        provides: type | None = None,
        kwargs: dict[str, Any] | None = None,
        scope: Scope | None = None,
        mode: RegisterMode = RegisterMode.RAISE_ON_CONFLICT,
    ) -> Decorator: ...

    def register(
        self,
        factory: FactoryT | None = None,
        *,
        provides: type | None = None,
        kwargs: dict[str, Any] | None = None,
        scope: Scope | None = None,
        mode: RegisterMode = RegisterMode.RAISE_ON_CONFLICT,
    ) -> FactoryT | Decorator:
        """Inject a factory into this container."""
        # Case 1: Decorator without arguments, i.e. @register
        if factory is not None:
            self.add(Provider(factory=factory))
            return factory

        # Case 2: Decorator with arguments, i.e. @register(...)
        def decorator(factory_: FactoryT) -> FactoryT:
            self.add(
                Provider(
                    factory=factory_,  # type: ignore[reportArgumentType]
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
        args: tuple = (),  # noqa: ARG002
        kwargs: dict[str, Any] | None = None,
    ) -> Any:
        providers = [
            result
            for strategy in self.strategies
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

    @staticmethod
    def _get_params(f: Callable | type) -> Mapping[str, inspect.Parameter]:
        try:
            sig = inspect.signature(f)
        except ValueError:
            sig = inspect.signature(f.__init__)
        return sig.parameters

    def call(
        self,
        function: Callable[..., T] | type[T],
        *,
        kwargs: dict[str, Any] | None = None,
    ) -> T:
        """Call a callable within the container's context."""
        provided_kwargs = kwargs or {}
        bound_args = {"self", "cls"}
        skip = bound_args.union(provided_kwargs)
        params = self._get_params(function)
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
            and name not in bound_args
        )
        return function(*positional_args, **build_kwargs)

    def extend(self) -> Self:
        """Return a new container extending the current context."""
        return type(self)(strategies=self.strategies, parent=self)
