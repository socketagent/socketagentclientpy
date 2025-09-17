"""
Socket Agent Client - Natural language interface for Socket Agent APIs.

This library provides a simple way to interact with Socket Agent APIs using
natural language queries processed by LLMs. Just ask questions and get results!

Basic usage:
    from socket_agent_client import SocketAgent

    agent = SocketAgent("http://localhost:8001")
    result = agent.ask("search for cheese")
"""

# Main natural language interface (primary)
from .agent import SocketAgent

# Legacy programmatic interface (for advanced use)
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
from .models import APIResponse, Descriptor, Endpoint
from .tools import generate_tools

__version__ = "0.1.0"

__all__ = [
    # Main natural language interface
    "SocketAgent",

    # Legacy programmatic interface (for advanced use)
    "Client",
    "fetch_descriptor",
    "Descriptor",
    "Endpoint",
    "APIResponse",
    "generate_tools",

    # Exceptions
    "SocketAgentError",
    "DiscoveryError",
    "ValidationError",
    "ExecutionError",
    "AuthenticationError",
    "TimeoutError",
    "RateLimitError",
]
