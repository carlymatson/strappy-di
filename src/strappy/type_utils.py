import types
from typing import Annotated, Any, Union, get_args, get_origin


def get_collection_type(hint) -> tuple[type | None, Any]:
    try:
        outer_type = get_origin(hint)
        if outer_type in (set, list, tuple):
            inner_type = get_args(hint)[0]
            return outer_type, inner_type
    except (TypeError, IndexError):
        pass
    return None, hint


def get_union_types(hint):
    outer_type = get_origin(hint)
    if outer_type in (types.UnionType, Union):
        return get_args(hint)
    return None


def unwrap_if_optional(hint):
    inner_types = get_union_types(hint)
    if inner_types is None:
        return hint
    if len(inner_types) == 2:
        return inner_types[0]
    non_null_types = [t for t in inner_types if t is not type(None)]
    return Union[*non_null_types]  # type: ignore #???


def unwrap_if_annotated(hint):
    outer_type = get_origin(hint)
    if outer_type == Annotated:
        return get_args(hint)[0]
    return hint


def unwrap_if_annotated_or_optional(hint):
    without_annotation = unwrap_if_annotated(hint)
    if without_annotation != hint:
        return without_annotation
    without_optionl = unwrap_if_optional(hint)
    if without_optionl != hint:
        return without_optionl
    return hint
