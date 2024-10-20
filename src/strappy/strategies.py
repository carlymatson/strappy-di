"""Strategies for getting a provider from a container and parameter."""

import inspect
from collections.abc import Collection, Hashable
from typing import Annotated, get_args, get_origin

from strappy import type_utils
from strappy.protocols import ContainerLike
from strappy.provider import Provider


def use_depends_meta_if_present(
    param: inspect.Parameter,
    container: ContainerLike,  # noqa: ARG001
) -> Provider | None:
    """Get FastAPI dependency resolver."""
    if get_origin(param.annotation) is Annotated:
        for annotation in get_args(param.annotation)[1:]:
            if hasattr(annotation, "dependency"):
                return Provider(factory=annotation.dependency)
    if hasattr(param.default, "dependency"):
        return Provider(factory=param.default.dependency)
    return None


def _search_for_subtypes(
    service: type,
    registry: dict[Hashable, list[Provider]],
) -> list[Provider] | None:
    # Looks up registered providers by progressively unwrapping type
    if service in registry:
        return registry[service]

    outer_type = service
    inner_type = type_utils.unwrap_if_annotated_or_optional(outer_type)
    while inner_type != outer_type:
        if inner_type in registry:
            return registry[inner_type]
        outer_type = inner_type
        inner_type = type_utils.unwrap_if_annotated_or_optional(outer_type)

    unioned_types = type_utils.get_union_types(inner_type)
    if unioned_types is not None:
        registered = [
            provider
            for subtype in unioned_types
            for provider in registry.get(subtype, [])
        ]
        if registered:
            return registered
    return None


def search_registry_for_type(
    param: inspect.Parameter,
    container: ContainerLike,
) -> Provider | None:
    """Search registry for parameter type or subtype and return registered provider."""
    providers = _search_for_subtypes(param.annotation, container.registry)
    if providers:
        return providers[0]
    return None


def search_registry_for_collection_inner_type(
    param: inspect.Parameter,
    container: ContainerLike,
) -> Provider | None:
    """Search registry for inner type and return collection provider."""
    annotation = param.annotation
    collection_type, inner_type = type_utils.get_collection_type(annotation)
    if collection_type is None:
        return None
    providers = _search_for_subtypes(inner_type, container.registry)
    if providers is None:
        return None

    def collection_factory(*args, **kwargs) -> Collection:  # noqa: ANN002, ANN003, ARG001
        return collection_type(
            provider.get(container, kwargs=kwargs) for provider in providers
        )

    return Provider(factory=collection_factory, provides=annotation)


def use_type_as_factory(
    param: inspect.Parameter,
    container: ContainerLike,  # noqa: ARG001
) -> Provider | None:
    """Get a provider which uses the type as a factory if valid."""
    hint = param.annotation
    if type_utils.is_concrete_class(hint):
        return Provider(param.annotation)
    return None
