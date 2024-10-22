"""Simple lightweight framework for dependency injection."""

from . import strategies as st
from .container import Container as Container
from .container import RegistrationMode as RegistrationMode
from .errors import RegistrationConflictError as RegistrationConflictError
from .errors import ResolutionError as ResolutionError
from .provider import Provider as Provider
from .provider import Scope as Scope

base = Container(
    strategies=(
        st.use_depends_meta_if_present,
        st.search_registry_for_type,
        st.search_registry_for_collection_inner_type,
        st.use_type_as_factory,
    ),
)
