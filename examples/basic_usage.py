#!/usr/bin/env python3
"""
Basic usage example for Socket Agent Client.

This example demonstrates how to use the client with a Socket Agent API.
"""

import json
from socket_agent_client import Client, TelemetryMiddleware


def main():
    """Run basic usage examples."""
    
    # Initialize client (adjust URL to your Socket Agent API)
    print("=== Initializing Socket Agent Client ===")
    client = Client("http://localhost:8001")
    
    # Get API information
    descriptor = client.get_descriptor()
    print(f"\nConnected to: {descriptor.name}")
    print(f"Description: {descriptor.description}")
    print(f"Version: {descriptor.version}")
    
    # List available endpoints
    print("\n=== Available Endpoints ===")
    endpoints = client.list_endpoints()
    for endpoint_name in endpoints[:5]:  # Show first 5
        endpoint = client.get_endpoint(endpoint_name)
        if endpoint:
            print(f"  - {endpoint_name}: {endpoint.summary}")
    
    # Get LLM tools
    print("\n=== LLM Tool Definitions ===")
    tools = client.get_tools(format="openai")
    print(f"Generated {len(tools)} OpenAI-compatible tools")
    
    # Show first tool as example
    if tools:
        print("\nExample tool definition:")
        print(json.dumps(tools[0], indent=2))
    
    # Add telemetry middleware
    print("\n=== Using Middleware ===")
    telemetry = TelemetryMiddleware(record_patterns=True)
    client.use_middleware(telemetry)
    print("Added telemetry middleware for pattern recording")
    
    # Make some API calls (adjust to match your API)
    print("\n=== Making API Calls ===")
    
    try:
        # Example: List products (adjust endpoint name as needed)
        print("\n1. Listing products...")
        response = client.call("list_products")
        if response.success:
            print(f"   Success! Got {len(response.data) if isinstance(response.data, list) else 1} items")
            print(f"   Response time: {response.duration_ms:.2f}ms")
        else:
            print(f"   Failed: {response.error}")
    except Exception as e:
        print(f"   Note: Adjust endpoint names to match your API. Error: {e}")
    
    try:
        # Example: Get specific item
        print("\n2. Getting specific product...")
        response = client.call("get_product", id="1")
        if response.success:
            print(f"   Success! Got product data")
            if isinstance(response.data, dict):
                print(f"   Product: {response.data.get('name', 'Unknown')}")
        else:
            print(f"   Failed: {response.error}")
    except Exception as e:
        print(f"   Note: Adjust endpoint names to match your API. Error: {e}")
    
    # Show recorded patterns
    print("\n=== Telemetry Patterns ===")
    patterns = telemetry.get_patterns()
    print(f"Recorded {len(patterns)} API calls")
    for pattern in patterns:
        print(f"  - {pattern['method']} {pattern['endpoint']}: "
              f"{pattern.get('duration_ms', 0):.2f}ms")
    
    # Raw API call example
    print("\n=== Raw API Call ===")
    try:
        response = client.call_raw(
            method="GET",
            path="/products",
            params={"limit": 5}
        )
        print(f"Raw call status: {response.status_code}")
    except Exception as e:
        print(f"Raw call failed: {e}")
    
    print("\n=== Example Complete ===")
    print("This example demonstrated:")
    print("  ✓ Connecting to a Socket Agent API")
    print("  ✓ Discovering available endpoints")
    print("  ✓ Generating LLM tool definitions")
    print("  ✓ Using middleware for telemetry")
    print("  ✓ Making API calls")
    print("  ✓ Recording patterns for future optimization")


if __name__ == "__main__":
    main()
