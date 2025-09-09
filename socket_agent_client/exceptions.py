"""Custom exceptions for Socket Agent client."""


class SocketAgentError(Exception):
    """Base exception for Socket Agent client errors."""
    pass


class DiscoveryError(SocketAgentError):
    """Error during descriptor discovery."""
    pass


class ValidationError(SocketAgentError):
    """Error validating data or schemas."""
    pass


class ExecutionError(SocketAgentError):
    """Error executing API call."""
    pass


class AuthenticationError(SocketAgentError):
    """Authentication failed."""
    pass


class TimeoutError(SocketAgentError):
    """Request timed out."""
    pass


class RateLimitError(SocketAgentError):
    """Rate limit exceeded."""
    pass
