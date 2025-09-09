"""LLM tool generation for Socket Agent APIs."""

from typing import Any, Dict, List, Optional

from .models import Descriptor, Endpoint


class ToolGenerator:
    """Generates LLM-compatible tool definitions from Socket Agent descriptors."""
    
    def __init__(self, descriptor: Descriptor):
        """
        Initialize tool generator.
        
        Args:
            descriptor: Socket Agent API descriptor
        """
        self.descriptor = descriptor
    
    def generate_openai_tools(self) -> List[Dict[str, Any]]:
        """
        Generate OpenAI-compatible function definitions.
        
        Returns:
            List of OpenAI function definitions
        """
        tools = []
        
        for endpoint in self.descriptor.endpoints:
            tool = {
                "type": "function",
                "function": {
                    "name": self._generate_function_name(endpoint),
                    "description": endpoint.summary,
                    "parameters": self._generate_openai_parameters(endpoint),
                }
            }
            tools.append(tool)
        
        return tools
    
    def generate_anthropic_tools(self) -> List[Dict[str, Any]]:
        """
        Generate Anthropic-compatible tool definitions.
        
        Returns:
            List of Anthropic tool definitions
        """
        tools = []
        
        for endpoint in self.descriptor.endpoints:
            tool = {
                "name": self._generate_function_name(endpoint),
                "description": endpoint.summary,
                "input_schema": self._generate_anthropic_schema(endpoint),
            }
            tools.append(tool)
        
        return tools
    
    def generate_generic_tools(self) -> List[Dict[str, Any]]:
        """
        Generate generic tool definitions.
        
        Returns:
            List of generic tool definitions
        """
        tools = []
        
        for endpoint in self.descriptor.endpoints:
            tool = {
                "name": self._generate_function_name(endpoint),
                "description": endpoint.summary,
                "method": endpoint.method,
                "path": endpoint.path,
                "parameters": self._extract_parameters(endpoint),
                "request_body": self._extract_request_body(endpoint),
            }
            tools.append(tool)
        
        return tools
    
    def _generate_function_name(self, endpoint: Endpoint) -> str:
        """
        Generate a function name from an endpoint.
        
        Args:
            endpoint: Endpoint to generate name for
            
        Returns:
            Function name
        """
        if endpoint.operationId:
            return endpoint.operationId
        
        # Generate from method and path
        path_parts = endpoint.path.strip("/").split("/")
        
        # Filter out parameter placeholders
        path_parts = [p for p in path_parts if not (p.startswith("{") and p.endswith("}"))]
        
        # Create name
        method_prefix = endpoint.method.lower()
        if method_prefix == "get":
            if "{" in endpoint.path:
                method_prefix = "get"
            else:
                method_prefix = "list"
        elif method_prefix == "post":
            method_prefix = "create"
        elif method_prefix == "put":
            method_prefix = "update"
        elif method_prefix == "patch":
            method_prefix = "patch"
        elif method_prefix == "delete":
            method_prefix = "delete"
        
        if path_parts:
            return f"{method_prefix}_{('_'.join(path_parts))}"
        
        return method_prefix
    
    def _generate_openai_parameters(self, endpoint: Endpoint) -> Dict[str, Any]:
        """
        Generate OpenAI-style parameters schema.
        
        Args:
            endpoint: Endpoint to generate parameters for
            
        Returns:
            OpenAI parameters schema
        """
        properties = {}
        required = []
        
        # Extract path parameters
        path_params = self._extract_path_parameters(endpoint.path)
        for param in path_params:
            properties[param] = {
                "type": "string",
                "description": f"Path parameter: {param}"
            }
            required.append(param)
        
        # Extract query parameters
        if endpoint.parameters:
            for param in endpoint.parameters:
                if param.get("in") == "query":
                    name = param.get("name")
                    properties[name] = {
                        "type": param.get("schema", {}).get("type", "string"),
                        "description": param.get("description", f"Query parameter: {name}")
                    }
                    if param.get("required"):
                        required.append(name)
        
        # Extract request body parameters
        if endpoint.requestBody:
            content = endpoint.requestBody.get("content", {})
            json_content = content.get("application/json", {})
            schema = json_content.get("schema", {})
            
            if schema.get("type") == "object":
                body_props = schema.get("properties", {})
                for prop_name, prop_schema in body_props.items():
                    properties[prop_name] = {
                        "type": prop_schema.get("type", "string"),
                        "description": prop_schema.get("description", f"Body parameter: {prop_name}")
                    }
                    if prop_name in schema.get("required", []):
                        required.append(prop_name)
        
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }
    
    def _generate_anthropic_schema(self, endpoint: Endpoint) -> Dict[str, Any]:
        """
        Generate Anthropic-style input schema.
        
        Args:
            endpoint: Endpoint to generate schema for
            
        Returns:
            Anthropic input schema
        """
        # Similar to OpenAI but with slightly different format
        return self._generate_openai_parameters(endpoint)
    
    def _extract_path_parameters(self, path: str) -> List[str]:
        """
        Extract parameter names from a path template.
        
        Args:
            path: Path template (e.g., "/users/{id}")
            
        Returns:
            List of parameter names
        """
        import re
        pattern = r"\{([^}]+)\}"
        return re.findall(pattern, path)
    
    def _extract_parameters(self, endpoint: Endpoint) -> List[Dict[str, Any]]:
        """
        Extract all parameters from an endpoint.
        
        Args:
            endpoint: Endpoint to extract parameters from
            
        Returns:
            List of parameter definitions
        """
        params = []
        
        # Path parameters
        path_params = self._extract_path_parameters(endpoint.path)
        for param in path_params:
            params.append({
                "name": param,
                "in": "path",
                "required": True,
                "type": "string"
            })
        
        # Query parameters
        if endpoint.parameters:
            for param in endpoint.parameters:
                if param.get("in") == "query":
                    params.append({
                        "name": param.get("name"),
                        "in": "query",
                        "required": param.get("required", False),
                        "type": param.get("schema", {}).get("type", "string"),
                        "description": param.get("description")
                    })
        
        return params
    
    def _extract_request_body(self, endpoint: Endpoint) -> Optional[Dict[str, Any]]:
        """
        Extract request body schema from an endpoint.
        
        Args:
            endpoint: Endpoint to extract body from
            
        Returns:
            Request body schema or None
        """
        if not endpoint.requestBody:
            return None
        
        content = endpoint.requestBody.get("content", {})
        json_content = content.get("application/json", {})
        return json_content.get("schema")


def generate_tools(descriptor: Descriptor, format: str = "openai") -> List[Dict[str, Any]]:
    """
    Generate LLM tools from a Socket Agent descriptor.
    
    Args:
        descriptor: Socket Agent API descriptor
        format: Tool format ("openai", "anthropic", or "generic")
        
    Returns:
        List of tool definitions
        
    Raises:
        ValueError: If format is not supported
    """
    generator = ToolGenerator(descriptor)
    
    if format == "openai":
        return generator.generate_openai_tools()
    elif format == "anthropic":
        return generator.generate_anthropic_tools()
    elif format == "generic":
        return generator.generate_generic_tools()
    else:
        raise ValueError(f"Unsupported format: {format}")
