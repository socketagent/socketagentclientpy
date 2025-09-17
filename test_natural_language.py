#!/usr/bin/env python3
"""
Test the new natural language SocketAgent interface.

This script tests the simplified natural language interface against
the Socket Agent APIs.
"""

import os
import sys
from socket_agent_client import SocketAgent
from socket_agent_client.exceptions import SocketAgentError


def test_grocery_api():
    """Test natural language queries against the grocery API."""
    print("=== Testing Natural Language Socket Agent ===\n")

    # Check if OpenAI API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY environment variable not set.")
        print("   Set it with: export OPENAI_API_KEY='your-key-here'")
        print("   Or pass api_key parameter to SocketAgent()")
        print()

    # Try to connect to grocery API
    try:
        print("1. Initializing SocketAgent for grocery API...")
        agent = SocketAgent("http://localhost:8001", llm="openai")

        api_info = agent.get_api_info()
        print(f"   ✓ Connected to: {api_info['name']}")
        print(f"   ✓ Description: {api_info['description']}")
        print(f"   ✓ Endpoints: {api_info['endpoints']}")
        print()

    except SocketAgentError as e:
        print(f"   ✗ Failed to initialize SocketAgent: {e}")
        print("\n   To test this, start the grocery API server:")
        print("   cd /home/deocy/socketagentpy/examples/benchmark/grocery_api")
        print("   python main.py")
        return False
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
        return False

    # Test natural language queries
    test_queries = [
        "search for cheese",
        "show me all products",
        "find products under $5",
        "what dairy products do you have?",
        "list all items in the store"
    ]

    print("2. Testing natural language queries...")
    for i, query in enumerate(test_queries, 1):
        print(f"\n   Query {i}: '{query}'")
        try:
            result = agent.ask(query)
            print(f"   ✓ Response: {result[:200]}{'...' if len(str(result)) > 200 else ''}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
            # Don't stop on individual query errors
            continue

    print("\n=== Natural Language Test Complete ===")
    return True


def test_api_info():
    """Test just the API info without OpenAI calls."""
    print("=== Testing API Discovery (No LLM) ===\n")

    try:
        print("Testing basic client functionality...")
        from socket_agent_client import Client

        client = Client("http://localhost:8001")
        descriptor = client.get_descriptor()
        tools = client.get_tools(format="openai")

        print(f"✓ API Name: {descriptor.name}")
        print(f"✓ Description: {descriptor.description}")
        print(f"✓ Endpoints: {len(descriptor.endpoints)}")
        print(f"✓ Generated Tools: {len(tools)}")

        print("\nExample tool:")
        if tools:
            tool = tools[0]
            print(f"  Name: {tool['function']['name']}")
            print(f"  Description: {tool['function']['description']}")

        print("\n✓ Basic functionality working!")
        return True

    except Exception as e:
        print(f"✗ Basic test failed: {e}")
        return False


def main():
    """Run the tests."""
    print("Socket Agent Natural Language Client Test")
    print("=" * 50)

    # First test basic functionality
    if not test_api_info():
        print("\nBasic functionality test failed. Check if grocery API is running.")
        return False

    print("\n" + "=" * 50)

    # Then test natural language if OpenAI key is available
    if os.getenv("OPENAI_API_KEY"):
        return test_grocery_api()
    else:
        print("Skipping OpenAI tests - no API key provided")
        print("Set OPENAI_API_KEY to test natural language features")
        return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)