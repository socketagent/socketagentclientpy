"""OpenAI LLM provider implementation."""

import os
from typing import Any, Dict, List, Optional

from .base import LLMProvider


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider using the official OpenAI client."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model to use (default: gpt-4)
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "OpenAI package not installed. Install with: pip install openai"
            )

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable or pass api_key parameter."
            )

        self.model = model
        self.client = OpenAI(api_key=self.api_key)

    def complete_with_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> Any:
        """
        Complete a chat conversation with access to tools.

        Args:
            messages: List of chat messages
            tools: List of OpenAI tool definitions

        Returns:
            OpenAI ChatCompletion response
        """
        try:
            # Filter out any tool messages that don't have tool_call_id for non-OpenAI messages
            filtered_messages = []
            for msg in messages:
                if msg["role"] == "tool" and "tool_call_id" not in msg:
                    # Skip malformed tool messages
                    continue
                filtered_messages.append(msg)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=filtered_messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None
            )

            return response.choices[0].message

        except Exception as e:
            raise RuntimeError(f"OpenAI API call failed: {e}")