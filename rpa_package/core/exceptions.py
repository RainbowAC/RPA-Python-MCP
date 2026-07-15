"""
RPA for Python - Custom Exceptions
"""


class RPAException(Exception):
    """Base exception for all RPA errors."""
    pass


class DesktopInitError(RPAException):
    """Raised when desktop automation initialization fails."""
    pass


class DesktopProcessError(RPAException):
    """Raised when desktop automation execution encounters an error."""
    pass


class ElementNotFoundError(RPAException):
    """Raised when a UI element cannot be found."""
    pass


class ConfigurationError(RPAException):
    """Raised for configuration-related errors."""
    pass