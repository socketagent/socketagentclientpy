"""Ollama LLM provider implementation."""

import json
import requests
from typing import Any, Dict, List, Optional

from .base import LLMProvider


class OllamaProvider(LLMProvider):
    """Ollama LLM provider for local models."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2:3b"):
        """
        Initialize Ollama provider.

        Args:
            base_url: Ollama API base URL (default: http://localhost:11434)
            model: Model name to use (default: llama3.2:3b)
        """
        self.base_url = base_url.rstrip("/")
        self.model = model

    def complete_with_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> Any:
        """
        Complete a chat conversation with access to tools using Ollama.

        Args:
            messages: List of chat messages
            tools: List of OpenAI-format tool definitions

        Returns:
            Response object with content and optional tool calls
        """
        try:
            # Convert OpenAI tools to Ollama format (simplified)
            ollama_tools = self._convert_tools_to_ollama(tools) if tools else None

            # Build the prompt for Ollama
            prompt = self._build_prompt(messages, ollama_tools)

            # Make request to Ollama
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "top_p": 0.9
                    }
                },
                timeout=30
            )
            response.raise_for_status()

            result = response.json()
            response_text = result.get("response", "")

            # Parse tool calls from response if any
            tool_calls = self._extract_tool_calls(response_text, tools) if tools else None

            return OllamaResponse(response_text, tool_calls)

        except Exception as e:
            raise RuntimeError(f"Ollama API call failed: {e}")

    def _convert_tools_to_ollama(self, openai_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert OpenAI tool format to Ollama-friendly descriptions."""
        ollama_tools = []
        for tool in openai_tools:
            func = tool.get("function", {})
            name = func.get("name", "unknown")
            description = func.get("description", "")

            # Simplified tool description for Ollama
            ollama_tools.append({
                "name": name,
                "description": description,
                "parameters": func.get("parameters", {})
            })
        return ollama_tools

    def _build_prompt(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]]) -> str:
        """Build a prompt for Ollama from OpenAI-format messages and tools."""

        # System message
        system_msg = ""
        user_msgs = []

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "system":
                system_msg = content
            elif role == "user":
                user_msgs.append(f"User: {content}")
            elif role == "assistant":
                user_msgs.append(f"Assistant: {content}")
            elif role == "tool":
                # Tool result - add to conversation
                user_msgs.append(f"Tool result: {content}")

        # Build tool descriptions
        tool_text = ""
        if tools:
            tool_text = "\n\nAvailable tools:\n"
            for tool in tools:
                name = tool.get("name", "")
                desc = tool.get("description", "")
                tool_text += f"- {name}: {desc}\n"

            tool_text += "\nTo use a tool, respond with: TOOL_CALL: {\"name\": \"tool_name\", \"arguments\": {\"param\": \"value\"}}"

        # Combine everything
        prompt = f"{system_msg}{tool_text}\n\n{chr(10).join(user_msgs)}\n\nAssistant:"

        return prompt

    def _extract_tool_calls(self, response_text: str, tools: List[Dict[str, Any]]) -> Optional[List]:
        """Extract tool calls from Ollama response text."""
        if not response_text or "TOOL_CALL:" not in response_text:
            return None

        try:
            # Look for TOOL_CALL: {"name": "...", "arguments": {...}}
            start = response_text.find("TOOL_CALL:")
            if start == -1:
                return None

            # Extract JSON after TOOL_CALL:
            json_start = response_text.find("{", start)
            if json_start == -1:
                return None

            # Find matching closing brace
            brace_count = 0
            json_end = json_start
            for i, char in enumerate(response_text[json_start:], json_start):
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i
                        break

            if brace_count != 0:
                return None

            # Parse the JSON
            json_text = response_text[json_start:json_end + 1]
            tool_call_data = json.loads(json_text)

            # Create tool call object
            return [OllamaToolCall(tool_call_data)]

        except Exception as e:
            print(f"Warning: Failed to parse tool call: {e}")
            return None


class OllamaResponse:
    """Response object that mimics OpenAI's response format."""

    def __init__(self, content: str, tool_calls: Optional[List] = None):
        self.content = content
        self.tool_calls = tool_calls


class OllamaToolCall:
    """Tool call object that mimics OpenAI's format."""

    def __init__(self, data: Dict[str, Any]):
        self.id = f"ollama_call_{hash(str(data))}"
        self.function = OllamaFunction(data)


class OllamaFunction:
    """Function call object that mimics OpenAI's format."""

    def __init__(self, data: Dict[str, Any]):
        self.name = data.get("name", "")
        self.arguments = json.dumps(data.get("arguments", {}))