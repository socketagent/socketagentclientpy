"""HTTP execution layer for Socket Agent client."""

import time
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import httpx

from .exceptions import AuthenticationError, ExecutionError, RateLimitError, TimeoutError
from .models import APIResponse, Endpoint


class Executor:
    """Handles HTTP requests to Socket Agent API endpoints."""
    
    DEFAULT_TIMEOUT = 30.0
    DEFAULT_MAX_RETRIES = 3
    
    def __init__(
        self,
        base_url: str,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        auth_token: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """
        Initialize executor.
        
        Args:
            base_url: Base URL for the API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            auth_token: Optional bearer token for authentication
            api_key: Optional API key for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.auth_token = auth_token
        self.api_key = api_key
    
    def execute(
        self,
        endpoint: Endpoint,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> APIResponse:
        """
        Execute an API call to an endpoint.
        
        Args:
            endpoint: Endpoint to call
            params: Query parameters for GET requests
            json_data: JSON body for POST/PUT/PATCH requests
            headers: Additional headers to include
            
        Returns:
            APIResponse with the result
        """
        # Build URL
        url = urljoin(self.base_url, endpoint.path)
        
        # Prepare headers
        final_headers = self._prepare_headers(headers)
        
        # Prepare request kwargs
        request_kwargs = {
            "method": endpoint.method,
            "url": url,
            "headers": final_headers,
        }
        
        # Add params or json based on method
        if endpoint.method in ["GET", "DELETE"]:
            if params:
                request_kwargs["params"] = params
        else:  # POST, PUT, PATCH
            if json_data:
                request_kwargs["json"] = json_data
            elif params:
                request_kwargs["json"] = params
        
        # Execute with retries
        return self._execute_with_retries(**request_kwargs)
    
    def call(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> APIResponse:
        """
        Execute a raw API call.
        
        Args:
            method: HTTP method
            path: URL path
            params: Query parameters
            json_data: JSON body
            headers: Additional headers
            
        Returns:
            APIResponse with the result
        """
        # Create a temporary endpoint
        endpoint = Endpoint(
            path=path,
            method=method,
            summary=f"{method} {path}"
        )
        
        return self.execute(endpoint, params, json_data, headers)
    
    def _prepare_headers(self, additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Prepare request headers including authentication.
        
        Args:
            additional_headers: Additional headers to include
            
        Returns:
            Complete headers dictionary
        """
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "socket-agent-client/0.1.0",
        }
        
        # Add authentication
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        
        # Add additional headers
        if additional_headers:
            headers.update(additional_headers)
        
        return headers
    
    def _execute_with_retries(self, **request_kwargs) -> APIResponse:
        """
        Execute request with retry logic.
        
        Args:
            **request_kwargs: Arguments for httpx.request
            
        Returns:
            APIResponse with the result
        """
        last_error = None
        start_time = time.time()
        
        for attempt in range(self.max_retries):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.request(**request_kwargs)
                    
                    # Calculate duration
                    duration_ms = (time.time() - start_time) * 1000
                    
                    # Handle rate limiting
                    if response.status_code == 429:
                        retry_after = response.headers.get("Retry-After", "60")
                        raise RateLimitError(f"Rate limited. Retry after {retry_after} seconds")
                    
                    # Handle authentication errors
                    if response.status_code in [401, 403]:
                        raise AuthenticationError(f"Authentication failed: {response.status_code}")
                    
                    # Parse response
                    return self._parse_response(response, duration_ms)
                    
            except httpx.TimeoutException as e:
                last_error = TimeoutError(f"Request timed out: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                    
            except (RateLimitError, AuthenticationError):
                raise
                
            except httpx.RequestError as e:
                last_error = ExecutionError(f"Request failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                    
            except Exception as e:
                last_error = ExecutionError(f"Unexpected error: {e}")
                break
        
        # All retries failed
        if last_error:
            raise last_error
        
        raise ExecutionError("Request failed after all retries")
    
    def _parse_response(self, response: httpx.Response, duration_ms: float) -> APIResponse:
        """
        Parse HTTP response into APIResponse.
        
        Args:
            response: HTTP response
            duration_ms: Request duration in milliseconds
            
        Returns:
            Parsed APIResponse
        """
        # Try to parse JSON
        try:
            if response.content:
                data = response.json()
            else:
                data = None
        except Exception:
            # Return raw text if not JSON
            data = response.text if response.text else None
        
        # Determine success
        success = 200 <= response.status_code < 400
        
        # Build error message if failed
        error = None
        if not success:
            if isinstance(data, dict):
                error = data.get("error") or data.get("message") or f"HTTP {response.status_code}"
            else:
                error = f"HTTP {response.status_code}: {response.reason_phrase}"
        
        return APIResponse(
            success=success,
            status_code=response.status_code,
            data=data,
            error=error,
            headers=dict(response.headers),
            duration_ms=duration_ms,
        )
