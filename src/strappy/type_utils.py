"""Utility functions for working with type hints."""

import inspect
import types
from typing import Annotated, Any, Protocol, Union, get_args, get_origin


def get_collection_type(hint: Any) -> tuple[type | None, Any]:
    """Get collection type and inner type from a type hint."""
    try:
        outer_type = get_origin(hint)
        if outer_type in (set, list, tuple):
            inner_type = get_args(hint)[0]
            return outer_type, inner_type
    except (TypeError, IndexError):
        pass
    return None, hint


def get_union_types(hint: Any) -> tuple[Any] | None:
    """Get types from a Union type hint."""
    outer_type = get_origin(hint)
    if outer_type in (types.UnionType, Union):
        return get_args(hint)
    return None


def unwrap_if_optional(hint: Any) -> Any:
    """Unwrap Optional type hint to inner type."""
    inner_types = get_union_types(hint)
    if inner_types is None:
        return hint
    if len(inner_types) == 2:  # noqa: PLR2004
        return inner_types[0]
    non_null_types = [t for t in inner_types if t is not type(None)]
    return Union[*non_null_types]  # type: ignore  # noqa: PGH003


def unwrap_if_annotated(hint: Any) -> Any:
    """Unwrap Annotated type hint to inner type."""
    outer_type = get_origin(hint)
    if outer_type == Annotated:
        return get_args(hint)[0]
    return hint


def unwrap_if_annotated_or_optional(hint: Any) -> Any:
    """Unwrap Annotated or Optional type hint to inner type."""
    without_annotation = unwrap_if_annotated(hint)
    if without_annotation != hint:
        return without_annotation
    without_optionl = unwrap_if_optional(hint)
    if without_optionl != hint:
        return without_optionl
    return hint


def is_concrete_class(hint: Any) -> bool:
    """Check if a type hint is a concrete class."""
    if hint == inspect._empty:  # noqa: SLF001
        return False
    try:
        is_class = inspect.isclass(hint)
        is_abstract = inspect.isabstract(hint)
        is_protocol = issubclass(hint, Protocol)
    except TypeError:
        return False
    return is_class and not (is_abstract or is_protocol)
