"""Simple lightweight framework for dependency injection."""

from .container import Container as Container
from .container import RegisterMode as RegisterMode
from .errors import RegistrationConflictError as RegistrationConflictError
from .errors import ResolutionError as ResolutionError
from .provider import Provider as Provider
from .provider import Scope as Scope

base = Container()
