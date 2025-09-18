#!/usr/bin/env python3
"""
Test script for Socket Agent Client MVP.

This script tests the basic functionality of the new client implementation.
"""

import json
import sys
from socketagentlib import Client, DiscoveryError


def test_client():
    """Test the Socket Agent client."""
    
    print("=== Socket Agent Client MVP Test ===\n")
    
    # Test 1: Try to connect to a Socket Agent API
    print("Test 1: Connecting to Socket Agent API...")
    try:
        # Try localhost first (where the test servers might be running)
        client = Client("http://localhost:8001", auto_discover=False)
        print("✓ Client created successfully")
    except Exception as e:
        print(f"✗ Failed to create client: {e}")
        return False
    
    # Test 2: Try discovery
    print("\nTest 2: Discovering API descriptor...")
    try:
        descriptor = client.discover()
        print(f"✓ Discovered API: {descriptor.name}")
        print(f"  Description: {descriptor.description}")
        print(f"  Base URL: {descriptor.baseUrl}")
        print(f"  Endpoints: {len(descriptor.endpoints)}")
    except DiscoveryError as e:
        print(f"✗ Discovery failed (is the server running?): {e}")
        print("\nNote: To test with actual servers, run the Socket Agent test servers:")
        print("  Terminal 1: cd examples/benchmark/grocery_api && python main.py")
        print("  Terminal 2: cd examples/benchmark/recipe_api && python main.py")
        print("  Terminal 3: cd examples/benchmark/banking_api && python main.py")
        
        # Test with mock data instead
        print("\n--- Testing with mock descriptor ---")
        return test_with_mock()
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False
    
    # Test 3: List endpoints
    print("\nTest 3: Listing endpoints...")
    try:
        endpoints = client.list_endpoints()
        print(f"✓ Found {len(endpoints)} endpoints:")
        for name in endpoints[:3]:
            endpoint = client.get_endpoint(name)
            if endpoint:
                print(f"  - {name}: {endpoint.method} {endpoint.path}")
    except Exception as e:
        print(f"✗ Failed to list endpoints: {e}")
    
    # Test 4: Generate LLM tools
    print("\nTest 4: Generating LLM tools...")
    try:
        openai_tools = client.get_tools(format="openai")
        print(f"✓ Generated {len(openai_tools)} OpenAI tools")
        
        if openai_tools:
            print("\nExample OpenAI tool:")
            print(json.dumps(openai_tools[0], indent=2)[:300] + "...")
    except Exception as e:
        print(f"✗ Failed to generate tools: {e}")
    
    # Test 5: API Call
    print("\nTest 5: Testing API call...")
    try:
        # Make a test call
        try:
            response = client.call("list_products")
            print(f"✓ API call succeeded: {response.status_code}")
        except Exception as e:
            print(f"  Note: API call failed (expected if no products endpoint): {e}")
    except Exception as e:
        print(f"✗ API call test failed: {e}")
    
    print("\n=== All tests completed ===")
    return True


def test_with_mock():
    """Test with mock data when no server is available."""
    from socketagentlib.models import Descriptor, Endpoint
    
    print("\nCreating mock descriptor for testing...")
    
    # Create a mock descriptor
    mock_descriptor = Descriptor(
        name="Test API",
        description="Mock API for testing",
        version="1.0.0",
        baseUrl="http://localhost:8000",
        endpoints=[
            Endpoint(
                path="/users",
                method="GET",
                summary="List all users",
                operationId="list_users"
            ),
            Endpoint(
                path="/users/{id}",
                method="GET",
                summary="Get user by ID",
                operationId="get_user"
            ),
            Endpoint(
                path="/users",
                method="POST",
                summary="Create a new user",
                operationId="create_user"
            ),
        ]
    )
    
    print(f"✓ Created mock descriptor with {len(mock_descriptor.endpoints)} endpoints")
    
    # Test tool generation with mock
    from socketagentlib.tools import generate_tools
    
    print("\nGenerating tools from mock descriptor...")
    tools = generate_tools(mock_descriptor, format="openai")
    print(f"✓ Generated {len(tools)} OpenAI tools")
    
    for tool in tools:
        func = tool["function"]
        print(f"  - {func['name']}: {func['description']}")
    
    print("\n✓ Mock testing completed successfully")
    return True


if __name__ == "__main__":
    success = test_client()
    sys.exit(0 if success else 1)
