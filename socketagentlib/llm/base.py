"""Base LLM provider interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class LLMProvider(ABC):
    """Base class for LLM providers."""

    @abstractmethod
    def complete_with_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> Any:
        """
        Complete a chat conversation with access to tools.

        Args:
            messages: List of chat messages
            tools: List of tool definitions

        Returns:
            Response object with content and optional tool calls
        """
        pass