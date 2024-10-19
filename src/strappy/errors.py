"""Exception types."""


class ResolutionError(Exception):
    """An error due to a missing dependency."""


class RegistrationConflictError(Exception):
    """A conflict while registering a provider."""


class InvalidProviderError(Exception):
    """Base exception for provider configuration errors."""


class NoImplementationError(InvalidProviderError):
    """Error when a Provider is instantiated with no factory or instance."""

    def __init__(self, *args: object) -> None:
        """Initialize exception."""
        message = "Must provide non-null value for either factory or instance."
        super().__init__(message, *args)


class MultipleImplementationsError(InvalidProviderError):
    """Error when a Provider is instantiated with both a factory and instance."""

    def __init__(self, *args: object) -> None:
        """Initialize exception."""
        message = "Cannot provide non-null values for both factory and instance."
        super().__init__(message, *args)


class TransientInstanceError(InvalidProviderError):
    """Error when a Provider is configured with an instance but is transient."""

    def __init__(self, *args: object) -> None:
        """Initialize exception."""
        message = "Providers configured with instances cannot be transient."
        super().__init__(message, *args)


class NoProviderTypeError(InvalidProviderError):
    """Error when a Provider is unable to determine its type."""

    def __init__(self, *args: object) -> None:
        """Initialize exception."""
        message = "Providers type could not be determined."
        super().__init__(message, *args)
