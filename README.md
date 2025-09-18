# Socket Agent Client

A clean, simple Python client library for Socket Agent APIs. This library makes it easy for LLM agents and applications to interact with Socket Agent-compliant APIs.

## Features

- 🚀 **Simple API** - Just point at a Socket Agent API and start making calls
- 🤖 **LLM-Ready** - Automatic generation of OpenAI/Anthropic tool definitions
- 🔌 **Extensible** - Middleware system for adding features like caching and telemetry
- 🔒 **Authentication** - Built-in support for Bearer tokens and API keys
- 📝 **Type-Safe** - Full type hints and Pydantic models
- 🎯 **Future-Proof** - Designed with pattern learning and optimization in mind

## Installation

```bash
pip install socketagentlib
```

## Quick Start

### Basic Usage

```python
from socketagentlib import Client

# Initialize client
client = Client("http://localhost:8001")

# List available endpoints
endpoints = client.list_endpoints()
print(f"Available endpoints: {endpoints}")

# Make an API call
response = client.call("list_products")
print(response.data)

# Call with parameters
response = client.call("get_product", id="123")
print(response.data)
```

### With Authentication

```python
from socketagentlib import Client

# With Bearer token
client = Client(
    "https://api.example.com",
    auth_token="your-bearer-token"
)

# With API key
client = Client(
    "https://api.example.com",
    api_key="your-api-key"
)
```

### LLM Integration

#### OpenAI

```python
from socketagentlib import Client
import openai

# Get OpenAI-compatible tools
client = Client("http://localhost:8001")
tools = client.get_tools(format="openai")

# Use with OpenAI
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "List all products"}],
    tools=tools,
    tool_choice="auto"
)

# Execute the function call
if response.choices[0].message.tool_calls:
    tool_call = response.choices[0].message.tool_calls[0]
    result = client.call(
        tool_call.function.name,
        **json.loads(tool_call.function.arguments)
    )
    print(result.data)
```

#### Anthropic

```python
from socketagentlib import Client

# Get Anthropic-compatible tools
client = Client("http://localhost:8001")
tools = client.get_tools(format="anthropic")

# Use with Anthropic Claude
# ... (similar to OpenAI example)
```

### Using Middleware

```python
from socketagentlib import Client, TelemetryMiddleware

client = Client("http://localhost:8001")

# Add telemetry middleware to track patterns
telemetry = TelemetryMiddleware(record_patterns=True)
client.use_middleware(telemetry)

# Make some calls
client.call("list_products")
client.call("create_product", name="Widget", price=9.99)

# Get recorded patterns (useful for future optimization)
patterns = telemetry.get_patterns()
print(f"Recorded {len(patterns)} API calls")
```

### Raw API Calls

```python
from socketagentlib import Client

client = Client("http://localhost:8001")

# Make a raw call without using the descriptor
response = client.call_raw(
    method="GET",
    path="/products",
    params={"category": "electronics"}
)
print(response.data)
```

## API Reference

### Client

```python
class Client:
    def __init__(
        base_url: str,
        auth_token: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        auto_discover: bool = True
    )
    
    def discover() -> Descriptor
    def get_descriptor() -> Descriptor
    def get_tools(format: str = "openai") -> List[Dict]
    def call(endpoint_name: str, **params) -> APIResponse
    def call_raw(method: str, path: str, ...) -> APIResponse
    def use_middleware(middleware: Middleware) -> None
    def list_endpoints() -> List[str]
```

### APIResponse

```python
class APIResponse:
    success: bool           # Whether the call succeeded
    status_code: int       # HTTP status code
    data: Any             # Response data
    error: Optional[str]  # Error message if failed
    headers: Dict[str, str]  # Response headers
    duration_ms: float    # Request duration
```

### Middleware

```python
from socketagentlib import Middleware

class CustomMiddleware(Middleware):
    def before_request(self, endpoint, params, context):
        # Modify request before sending
        return params, context
    
    def after_response(self, endpoint, response, context):
        # Modify response after receiving
        return response
    
    def on_error(self, endpoint, error, context):
        # Handle errors
        return error
```

## Architecture

The client is designed with a clean, extensible architecture:

```
┌─────────────┐
│   Client    │ ← Main interface
└─────┬───────┘
      │
      ├── Discovery  → Fetches Socket Agent descriptors
      ├── Executor   → Handles HTTP requests
      ├── Tools      → Generates LLM tool definitions
      └── Middleware → Extensible request/response pipeline
```

## Future Features

This MVP is designed to be extended with:

- **Pattern Learning** - Learn common API usage patterns to optimize future calls
- **Smart Caching** - Cache responses based on endpoint characteristics
- **Request Routing** - Route high-confidence patterns directly without LLM
- **Token Optimization** - Reduce LLM token usage over time

The middleware system provides clean extension points for these features without breaking the existing API.

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/socketagent/socket-agent-client.git
cd socket-agent-client

# Install in development mode
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Format code
black socket_agent_client/

# Type checking
mypy socket_agent_client/

# Linting
ruff socket_agent_client/
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Links

- [Socket Agent Specification](https://github.com/systemshift/socket-agent)
- [Examples](examples/)
- [API Documentation](https://docs.socketagent.io)
