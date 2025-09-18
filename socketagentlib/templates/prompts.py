"""System prompt templates for Socket Agent LLM integration."""

from typing import Any, Dict, List

from ..models import Descriptor


SYSTEM_PROMPT_TEMPLATE = """You are an AI assistant that can interact with the {api_name} API to help users with their requests.

API Information:
- Name: {api_name}
- Description: {api_description}
- Base URL: {base_url}

You have access to the following functions that allow you to interact with this API:

{tool_descriptions}

Instructions:
1. When a user makes a request, determine which function(s) would be most helpful to fulfill their request
2. Use the functions to gather information or perform actions as needed
3. If you need to make multiple API calls, do so in a logical order
4. Always provide a helpful summary of the results in natural language
5. If an API call fails, explain what went wrong and suggest alternatives if possible
6. Be conversational and helpful - users shouldn't need to know the technical details of the API

Remember:
- Use the exact function names provided
- Follow the parameter requirements for each function
- Handle errors gracefully and explain them in simple terms
- Focus on helping the user achieve their goal, not just returning raw API data"""


def build_system_prompt(descriptor: Descriptor, tools: List[Dict[str, Any]]) -> str:
    """
    Build a system prompt from API descriptor and tools.

    Args:
        descriptor: Socket Agent API descriptor
        tools: List of tool definitions

    Returns:
        Formatted system prompt string
    """
    # Extract API information
    api_name = descriptor.name or "API"
    api_description = descriptor.description or "No description available"
    base_url = str(descriptor.baseUrl) if descriptor.baseUrl else "Not specified"

    # Build tool descriptions
    tool_descriptions = []
    for tool in tools:
        func = tool.get("function", {})
        name = func.get("name", "unknown")
        description = func.get("description", "No description")

        # Extract parameter info
        parameters = func.get("parameters", {})
        properties = parameters.get("properties", {})
        required = parameters.get("required", [])

        param_details = []
        for param_name, param_info in properties.items():
            param_type = param_info.get("type", "unknown")
            param_desc = param_info.get("description", "")
            is_required = param_name in required
            req_text = " (required)" if is_required else " (optional)"
            param_details.append(f"  - {param_name} ({param_type}){req_text}: {param_desc}")

        param_text = "\n".join(param_details) if param_details else "  No parameters"

        tool_descriptions.append(f"• {name}: {description}\n{param_text}")

    tool_descriptions_text = "\n\n".join(tool_descriptions) if tool_descriptions else "No functions available"

    return SYSTEM_PROMPT_TEMPLATE.format(
        api_name=api_name,
        api_description=api_description,
        base_url=base_url,
        tool_descriptions=tool_descriptions_text
    )


def build_error_explanation(error_msg: str, context: str = "") -> str:
    """
    Build a user-friendly error explanation.

    Args:
        error_msg: Technical error message
        context: Additional context about what was being attempted

    Returns:
        User-friendly error explanation
    """
    base_msg = "I encountered an issue while trying to help you."

    if context:
        base_msg += f" I was attempting to {context}."

    # Try to make common errors more user-friendly
    if "404" in error_msg or "not found" in error_msg.lower():
        explanation = "The requested resource wasn't found. It might not exist or might have been moved."
    elif "401" in error_msg or "unauthorized" in error_msg.lower():
        explanation = "I don't have permission to access this resource. You might need to log in or check your credentials."
    elif "403" in error_msg or "forbidden" in error_msg.lower():
        explanation = "Access to this resource is forbidden. You might not have the necessary permissions."
    elif "500" in error_msg or "internal server error" in error_msg.lower():
        explanation = "The server encountered an internal error. This is usually a temporary issue."
    elif "timeout" in error_msg.lower():
        explanation = "The request took too long to complete. The server might be busy or temporarily unavailable."
    else:
        explanation = f"Here's what happened: {error_msg}"

    return f"{base_msg}\n\n{explanation}\n\nPlease let me know if you'd like to try something else or if you need help with a different request."