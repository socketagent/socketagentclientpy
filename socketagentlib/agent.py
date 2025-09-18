"""
Natural Language Socket Agent Client.

This is the main interface for interacting with Socket Agent APIs using natural language.
"""

import json
from typing import Any, Dict, List, Optional

from .client import Client
from .exceptions import SocketAgentError


class SocketAgent:
    """
    Natural language interface for Socket Agent APIs.

    This class provides a simple way to interact with Socket Agent APIs using
    natural language queries that are processed by an LLM and converted to API calls.
    """

    def __init__(
        self,
        base_url: str,
        llm: str = "openai",
        api_key: Optional[str] = None,
        timeout: float = 30.0
    ):
        """
        Initialize the Socket Agent.

        Args:
            base_url: Base URL of the Socket Agent API
            llm: LLM provider ("openai", "anthropic", "ollama")
            api_key: API key for the LLM provider
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.llm_type = llm
        self.api_key = api_key

        # Initialize the internal client
        self.client = Client(base_url, timeout=timeout)

        # Get API descriptor and tools
        try:
            self.descriptor = self.client.get_descriptor()
            self.tools = self.client.get_tools(format="openai")  # Start with OpenAI format
        except Exception as e:
            raise SocketAgentError(f"Failed to initialize Socket Agent: {e}")

        # Initialize LLM provider (lazy)
        self._llm_provider = None

        # Create system prompt
        self.system_prompt = self._build_system_prompt()

        # Conversation history
        self.conversation_history: List[Dict[str, Any]] = []

    @property
    def llm_provider(self):
        """Get LLM provider, creating it lazily."""
        if self._llm_provider is None:
            self._llm_provider = self._create_llm_provider()
        return self._llm_provider

    @llm_provider.setter
    def llm_provider(self, provider):
        """Set LLM provider directly."""
        self._llm_provider = provider

    def ask(self, question: str) -> Any:
        """
        Ask a natural language question and get results.

        Args:
            question: Natural language question/request

        Returns:
            The result of processing the question

        Raises:
            SocketAgentError: If the request fails
        """
        try:
            # Add user question to conversation
            messages = [
                {"role": "system", "content": self.system_prompt},
                *self.conversation_history,
                {"role": "user", "content": question}
            ]

            # Send to LLM with tools
            response = self.llm_provider.complete_with_tools(messages, self.tools)

            # Process tool calls if any
            if hasattr(response, 'tool_calls') and response.tool_calls:
                tool_results = []
                for tool_call in response.tool_calls:
                    result = self._execute_tool_call(tool_call)
                    tool_results.append(result)

                # Add assistant message with tool calls
                messages.append({
                    "role": "assistant",
                    "content": response.content or "",
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments
                            }
                        } for tool_call in response.tool_calls
                    ]
                })

                # Add tool results
                for i, tool_call in enumerate(response.tool_calls):
                    messages.append({
                        "role": "tool",
                        "content": json.dumps(tool_results[i]),
                        "tool_call_id": tool_call.id
                    })

                # Get final response from LLM
                final_response = self.llm_provider.complete_with_tools(messages, self.tools)
                result = final_response.content
            else:
                result = response.content

            # Update conversation history (keep last 10 messages)
            self.conversation_history.extend([
                {"role": "user", "content": question},
                {"role": "assistant", "content": result}
            ])
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]

            return result

        except Exception as e:
            raise SocketAgentError(f"Failed to process question: {e}")

    def _create_llm_provider(self):
        """Create the appropriate LLM provider."""
        if self.llm_type == "openai":
            from .llm.openai import OpenAIProvider
            return OpenAIProvider(api_key=self.api_key)
        elif self.llm_type == "anthropic":
            from .llm.anthropic import AnthropicProvider
            return AnthropicProvider(api_key=self.api_key)
        elif self.llm_type == "ollama":
            from .llm.ollama import OllamaProvider
            return OllamaProvider()
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_type}")

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the LLM."""
        from .templates.prompts import build_system_prompt
        return build_system_prompt(self.descriptor, self.tools)

    def _execute_tool_call(self, tool_call) -> Dict[str, Any]:
        """
        Execute a tool call from the LLM.

        Args:
            tool_call: Tool call object from LLM

        Returns:
            Result of the API call
        """
        try:
            # Parse arguments
            if isinstance(tool_call.function.arguments, str):
                args = json.loads(tool_call.function.arguments)
            else:
                args = tool_call.function.arguments

            # Execute via client
            response = self.client.call(tool_call.function.name, **args)

            if response.success:
                return {
                    "success": True,
                    "data": response.data,
                    "status_code": response.status_code
                }
            else:
                return {
                    "success": False,
                    "error": response.error,
                    "status_code": response.status_code
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": 0
            }

    def reset_conversation(self):
        """Reset the conversation history."""
        self.conversation_history = []

    def get_api_info(self) -> Dict[str, Any]:
        """Get information about the connected API."""
        return {
            "name": self.descriptor.name,
            "description": self.descriptor.description,
            "version": getattr(self.descriptor, 'version', 'unknown'),
            "base_url": self.descriptor.baseUrl or self.base_url,
            "endpoints": len(self.descriptor.endpoints)
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"<SocketAgent: {self.descriptor.name} via {self.llm_type}>"