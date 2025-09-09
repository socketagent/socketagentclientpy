"""
Socket Agent Client - A clean, simple client for Socket Agent APIs.

This library provides an easy way to interact with Socket Agent APIs,
with built-in support for LLM tool generation and extensible middleware
for future features like caching and pattern learning.
"""

from .client import Client
from .discovery import fetch_descriptor
from .exceptions import (
    AuthenticationError,
    DiscoveryError,
    ExecutionError,
    RateLimitError,
    SocketAgentError,
    TimeoutError,
    ValidationError,
)
from .middleware import CacheMiddleware, Middleware, TelemetryMiddleware
from .models import APIResponse, Descriptor, Endpoint
from .tools import generate_tools

__version__ = "0.1.0"

__all__ = [
    # Main client
    "Client",
    # Discovery
    "fetch_descriptor",
    # Models
    "Descriptor",
    "Endpoint",
    "APIResponse",
    # Tools
    "generate_tools",
    # Middleware
    "Middleware",
    "TelemetryMiddleware",
    "CacheMiddleware",
    # Exceptions
    "SocketAgentError",
    "DiscoveryError",
    "ValidationError",
    "ExecutionError",
    "AuthenticationError",
    "TimeoutError",
    "RateLimitError",
]
