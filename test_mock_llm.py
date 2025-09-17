#!/usr/bin/env python3
"""
Test the natural language interface with a mock LLM.

This demonstrates the complete flow without requiring an actual LLM API key.
"""

import json
from socket_agent_client import SocketAgent
from socket_agent_client.llm.base import LLMProvider


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing without API keys."""

    def __init__(self):
        self.call_count = 0

    def complete_with_tools(self, messages, tools):
        """Mock LLM response that calls list_products first, then summarizes."""
        self.call_count += 1

        # Get the last user message
        user_msg = None
        for msg in reversed(messages):
            if msg["role"] == "user":
                user_msg = msg["content"]
                break

        print(f"   🤖 Mock LLM call #{self.call_count}, received: '{user_msg or 'follow-up'}'")

        # Check if this is a follow-up call (has tool results)
        has_tool_results = any(msg["role"] == "tool" for msg in messages)

        if has_tool_results:
            # Second call: summarize the tool results
            print("   🤖 Mock LLM providing final summary...")
            class MockResponse:
                def __init__(self):
                    self.content = "I found all the products in the grocery store! Here's what's available: various groceries including produce, dairy, and other items."
                    self.tool_calls = None

            return MockResponse()
        else:
            # First call: make a tool call
            print("   🤖 Mock LLM calling list_products tool...")
            class MockToolCall:
                def __init__(self):
                    self.id = "mock_call_123"
                    self.function = MockFunction()

            class MockFunction:
                def __init__(self):
                    self.name = "list_products"
                    self.arguments = "{}"

            class MockResponse:
                def __init__(self):
                    self.content = ""
                    self.tool_calls = [MockToolCall()]

            return MockResponse()


def test_mock_natural_language():
    """Test with mock LLM to show complete flow."""
    print("=== Testing Natural Language Flow with Mock LLM ===\n")

    try:
        # Create SocketAgent but replace its LLM provider
        agent = SocketAgent("http://localhost:8001", llm="openai")

        # Replace with our mock provider
        agent.llm_provider = MockLLMProvider()

        print("✓ SocketAgent initialized with mock LLM")
        print(f"✓ Connected to: {agent.get_api_info()['name']}")

        # Test natural language query
        print(f"\n🔍 User asks: 'search for cheese'")
        result = agent.ask("search for cheese")

        print(f"✓ Final result: {result}")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_mock_natural_language()
    print(f"\n{'✓ Test passed!' if success else '✗ Test failed!'}")