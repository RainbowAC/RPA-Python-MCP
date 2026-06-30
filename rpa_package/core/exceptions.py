"""
RPA for Python - Custom Exceptions
"""

class RPAException(Exception):
    """Base exception for all RPA errors."""
    pass


class TagUIInitError(RPAException):
    """Raised when TagUI initialization fails."""
    pass


class TagUIProcessError(RPAException):
    """Raised when the TagUI process encounters an error."""
    pass


class ElementNotFoundError(RPAException):
    """Raised when a UI element cannot be found."""
    pass


class ConfigurationError(RPAException):
    """Raised for configuration-related errors."""
    pass