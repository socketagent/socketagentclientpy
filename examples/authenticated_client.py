"""
Example of using socketagentlib with authentication.

This example demonstrates:
1. Discovering an authenticated socket-agent API
2. Authenticating with socketagent.id
3. Making authenticated API calls
4. Automatic token refresh

Usage:
1. Start socketagent.id: `cd ../../../socketagent.id && ./socketagent-id`
2. Start authenticated todo API: `cd ../../../socketagentpy/examples/authenticated_todo && python main.py`
3. Run this script: `python authenticated_client.py`
"""

import asyncio
import json

from socketagentlib import Client


async def register_user(identity_url: str, username: str, password: str):
    """Register a new user with socketagent.id."""
    import httpx

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{identity_url}/v1/users",
            json={
                "username": username,
                "password": password,
                "email": f"{username}@example.com"
            }
        )

        if response.status_code == 200:
            print(f"✅ User {username} registered successfully")
            return response.json()
        elif response.status_code == 409:
            print(f"ℹ️  User {username} already exists")
            return None
        else:
            print(f"❌ Failed to register user: {response.status_code} - {response.text}")
            return None


async def demo_authenticated_client():
    """Demonstrate authenticated client usage."""
    print("🚀 Socket Agent Authentication Demo")
    print("=" * 50)

    # Configuration
    api_url = "http://localhost:8001"
    identity_url = "http://localhost:8080"
    username = "demo_user"
    password = "demo_password123"

    # Step 1: Register user (if needed)
    print("\n1️⃣  Registering demo user...")
    await register_user(identity_url, username, password)

    # Step 2: Create client and discover API
    print("\n2️⃣  Creating client and discovering API...")
    client = Client(
        base_url=api_url,
        identity_service_url=identity_url,
        auto_discover=True
    )

    # Print descriptor info
    descriptor = client.get_descriptor()
    print(f"   📝 API: {descriptor.name}")
    print(f"   📄 Description: {descriptor.description}")
    print(f"   🔐 Auth required: {descriptor.auth.type if descriptor.auth else 'none'}")

    # Step 3: Authenticate
    print(f"\n3️⃣  Authenticating as {username}...")
    try:
        await client.authenticate(username, password)
        print("   ✅ Authentication successful!")
    except Exception as e:
        print(f"   ❌ Authentication failed: {e}")
        return

    # Step 4: List available endpoints
    print("\n4️⃣  Available endpoints:")
    endpoints = client.list_endpoints()
    for endpoint in endpoints:
        print(f"   • {endpoint}")

    # Step 5: Test API calls
    print("\n5️⃣  Testing API calls...")

    try:
        # Create a todo
        print("\n   📝 Creating a todo...")
        todo_response = client.call("create_todos", text="Buy groceries", priority="high")
        if todo_response.success:
            todo = todo_response.data
            print(f"   ✅ Todo created: {todo['text']} (ID: {todo['id']})")
        else:
            print(f"   ❌ Failed to create todo: {todo_response.error}")
            return

        # List todos
        print("\n   📋 Listing todos...")
        list_response = client.call("list_todos")
        if list_response.success:
            todos = list_response.data
            print(f"   ✅ Found {len(todos)} todos:")
            for todo in todos:
                status = "✓" if todo["completed"] else "○"
                print(f"      {status} {todo['text']} ({todo['priority']} priority)")
        else:
            print(f"   ❌ Failed to list todos: {list_response.error}")

        # Create another todo
        print("\n   📝 Creating another todo...")
        todo2_response = client.call("create_todos", text="Write documentation", priority="medium")
        if todo2_response.success:
            todo2 = todo2_response.data
            print(f"   ✅ Todo created: {todo2['text']} (ID: {todo2['id']})")

        # List todos again
        print("\n   📋 Listing todos again...")
        list_response2 = client.call("list_todos")
        if list_response2.success:
            todos = list_response2.data
            print(f"   ✅ Found {len(todos)} todos total")

        # Delete a todo
        if todo_response.success:
            print(f"\n   🗑️  Deleting todo {todo['id']}...")
            delete_response = client.call("delete_todo", todo_id=todo["id"])
            if delete_response.success:
                print("   ✅ Todo deleted successfully")
            else:
                print(f"   ❌ Failed to delete todo: {delete_response.error}")

    except Exception as e:
        print(f"   ❌ API call failed: {e}")

    # Step 6: Test authentication status
    print(f"\n6️⃣  Authentication status: {'✅ Authenticated' if client.is_authenticated() else '❌ Not authenticated'}")

    # Step 7: Logout
    print("\n7️⃣  Logging out...")
    await client.logout()
    print(f"   Authentication status: {'✅ Authenticated' if client.is_authenticated() else '❌ Not authenticated'}")

    print("\n🎉 Demo completed!")


async def demo_tool_generation():
    """Demonstrate tool generation for LLMs."""
    print("\n" + "=" * 50)
    print("🔧 LLM Tool Generation Demo")
    print("=" * 50)

    client = Client("http://localhost:8001", auto_discover=True)

    # Generate OpenAI-compatible tools
    print("\n📄 OpenAI-compatible tools:")
    try:
        openai_tools = client.get_tools(format="openai")
        print(json.dumps(openai_tools, indent=2))
    except Exception as e:
        print(f"❌ Failed to generate tools: {e}")


if __name__ == "__main__":
    print("Make sure the following services are running:")
    print("1. socketagent.id on http://localhost:8080")
    print("2. Authenticated todo API on http://localhost:8001")
    print("\nPress Enter to continue or Ctrl+C to exit...")

    try:
        input()
        asyncio.run(demo_authenticated_client())
        asyncio.run(demo_tool_generation())
    except KeyboardInterrupt:
        print("\nDemo cancelled.")
    except Exception as e:
        print(f"\nDemo failed: {e}")
        print("Make sure all services are running and accessible.")