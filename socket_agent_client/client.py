"""Main client for Socket Agent APIs."""

from typing import Any, Dict, List, Optional

from .discovery import fetch_descriptor
from .exceptions import SocketAgentError, ValidationError
from .executor import Executor
from .middleware.base import Middleware
from .models import APIResponse, Descriptor, Endpoint
from .tools import generate_tools


class Client:
    """
    Socket Agent API client.
    
    A clean, simple client for interacting with Socket Agent APIs.
    Designed to be easily extensible with middleware for future features
    like caching and pattern learning.
    """
    
    def __init__(
        self,
        base_url: str,
        auth_token: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        auto_discover: bool = True,
    ):
        """
        Initialize Socket Agent client.
        
        Args:
            base_url: Base URL of the Socket Agent API
            auth_token: Optional bearer token for authentication
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
            auto_discover: Whether to fetch descriptor on initialization
        """
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token
        self.api_key = api_key
        self.timeout = timeout
        
        # Core components
        self.descriptor: Optional[Descriptor] = None
        self.executor: Optional[Executor] = None
        self.middlewares: List[Middleware] = []
        
        # Endpoint lookup cache
        self._endpoint_cache: Dict[str, Endpoint] = {}
        
        # Auto-discover if requested
        if auto_discover:
            self.discover()
    
    def discover(self) -> Descriptor:
        """
        Fetch and parse the Socket Agent descriptor.
        
        Returns:
            The parsed descriptor
            
        Raises:
            DiscoveryError: If discovery fails
        """
        self.descriptor = fetch_descriptor(self.base_url, timeout=self.timeout)
        
        # Initialize executor with discovered base URL
        base_url = str(self.descriptor.baseUrl) if self.descriptor.baseUrl else self.base_url
        self.executor = Executor(
            base_url=base_url,
            timeout=self.timeout,
            auth_token=self.auth_token,
            api_key=self.api_key,
        )
        
        # Build endpoint cache for quick lookup
        self._build_endpoint_cache()
        
        return self.descriptor
    
    def get_descriptor(self) -> Descriptor:
        """
        Get the API descriptor.
        
        Returns:
            The descriptor
            
        Raises:
            SocketAgentError: If not discovered yet
        """
        if not self.descriptor:
            raise SocketAgentError("Descriptor not fetched. Call discover() first.")
        return self.descriptor
    
    def get_tools(self, format: str = "openai") -> List[Dict[str, Any]]:
        """
        Get LLM-compatible tool definitions.
        
        Args:
            format: Tool format ("openai", "anthropic", or "generic")
            
        Returns:
            List of tool definitions
            
        Raises:
            SocketAgentError: If not discovered yet
            ValueError: If format is not supported
        """
        if not self.descriptor:
            raise SocketAgentError("Descriptor not fetched. Call discover() first.")
        
        return generate_tools(self.descriptor, format=format)
    
    def call(
        self,
        endpoint_name: str,
        **params: Any
    ) -> APIResponse:
        """
        Call an API endpoint by name.
        
        Args:
            endpoint_name: Name of the endpoint (operationId or generated name)
            **params: Parameters to pass to the endpoint
            
        Returns:
            APIResponse with the result
            
        Raises:
            SocketAgentError: If not discovered yet
            ValidationError: If endpoint not found
            ExecutionError: If the call fails
        """
        if not self.descriptor or not self.executor:
            raise SocketAgentError("Client not initialized. Call discover() first.")
        
        # Find endpoint
        endpoint = self._find_endpoint(endpoint_name)
        if not endpoint:
            raise ValidationError(f"Endpoint not found: {endpoint_name}")
        
        # Apply middleware before request
        context = {}
        for middleware in self.middlewares:
            modified_params, modified_context = middleware.before_request(
                endpoint, params, context
            )
            if modified_params is not None:
                params = modified_params
            if modified_context is not None:
                context = modified_context
        
        # Execute request
        try:
            response = self.executor.execute(endpoint, params)
        except Exception as e:
            # Let middleware handle errors
            for middleware in self.middlewares:
                e = middleware.on_error(endpoint, e, context)
                if e is None:
                    break
            if e:
                raise e
            # Error was suppressed
            response = APIResponse(
                success=False,
                status_code=0,
                data=None,
                error="Error suppressed by middleware"
            )
        
        # Apply middleware after response
        for middleware in self.middlewares:
            response = middleware.after_response(endpoint, response, context)
        
        return response
    
    def call_raw(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> APIResponse:
        """
        Make a raw API call without using the descriptor.
        
        Args:
            method: HTTP method
            path: URL path
            params: Query parameters
            json_data: JSON body
            headers: Additional headers
            
        Returns:
            APIResponse with the result
        """
        if not self.executor:
            # Create executor if not initialized
            self.executor = Executor(
                base_url=self.base_url,
                timeout=self.timeout,
                auth_token=self.auth_token,
                api_key=self.api_key,
            )
        
        return self.executor.call(method, path, params, json_data, headers)
    
    def use_middleware(self, middleware: Middleware) -> None:
        """
        Add middleware to the client.
        
        Middleware can intercept and modify requests/responses,
        enabling features like caching, telemetry, and pattern learning.
        
        Args:
            middleware: Middleware instance to add
        """
        self.middlewares.append(middleware)
    
    def remove_middleware(self, middleware: Middleware) -> None:
        """
        Remove middleware from the client.
        
        Args:
            middleware: Middleware instance to remove
        """
        if middleware in self.middlewares:
            self.middlewares.remove(middleware)
    
    def list_endpoints(self) -> List[str]:
        """
        List all available endpoint names.
        
        Returns:
            List of endpoint names
            
        Raises:
            SocketAgentError: If not discovered yet
        """
        if not self.descriptor:
            raise SocketAgentError("Descriptor not fetched. Call discover() first.")
        
        return list(self._endpoint_cache.keys())
    
    def get_endpoint(self, name: str) -> Optional[Endpoint]:
        """
        Get endpoint details by name.
        
        Args:
            name: Endpoint name
            
        Returns:
            Endpoint object or None if not found
        """
        return self._find_endpoint(name)
    
    def _build_endpoint_cache(self) -> None:
        """Build cache of endpoints for quick lookup."""
        if not self.descriptor:
            return
        
        self._endpoint_cache.clear()
        
        for endpoint in self.descriptor.endpoints:
            # Use operationId if available
            if endpoint.operationId:
                self._endpoint_cache[endpoint.operationId] = endpoint
            
            # Also create a generated name
            name = self._generate_endpoint_name(endpoint)
            self._endpoint_cache[name] = endpoint
            
            # Also store by method:path
            key = f"{endpoint.method}:{endpoint.path}"
            self._endpoint_cache[key] = endpoint
    
    def _generate_endpoint_name(self, endpoint: Endpoint) -> str:
        """Generate a name for an endpoint."""
        # Similar to tools.py logic
        path_parts = endpoint.path.strip("/").split("/")
        path_parts = [p for p in path_parts if not (p.startswith("{") and p.endswith("}"))]
        
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
    
    def _find_endpoint(self, name: str) -> Optional[Endpoint]:
        """Find an endpoint by name."""
        return self._endpoint_cache.get(name)
    
    def __repr__(self) -> str:
        """String representation."""
        if self.descriptor:
            return f"<SocketAgentClient: {self.descriptor.name}>"
        return f"<SocketAgentClient: {self.base_url}>"
