"""Simple lightweight framework for dependency injection."""
# ruff: noqa: F401

from .container import Container, RegisterMode
from .errors import RegistrationConflictError, ResolutionError
from .provider import Provider, Scope

base = Container()
