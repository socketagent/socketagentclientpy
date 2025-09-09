"""Base middleware interface for Socket Agent client."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ..models import APIResponse, Endpoint


class Middleware(ABC):
    """
    Abstract base class for middleware.
    
    Middleware can intercept and modify requests and responses,
    enabling features like logging, telemetry, caching, and pattern learning.
    """
    
    @abstractmethod
    def before_request(
        self,
        endpoint: Endpoint,
        params: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Called before a request is executed.
        
        Args:
            endpoint: The endpoint being called
            params: Request parameters
            context: Additional context
            
        Returns:
            Tuple of (modified_params, modified_context)
            Return (None, None) to skip modification
        """
        pass
    
    @abstractmethod
    def after_response(
        self,
        endpoint: Endpoint,
        response: APIResponse,
        context: Optional[Dict[str, Any]] = None,
    ) -> APIResponse:
        """
        Called after a response is received.
        
        Args:
            endpoint: The endpoint that was called
            response: The response received
            context: Additional context
            
        Returns:
            Modified response (or original if no changes)
        """
        pass
    
    def on_error(
        self,
        endpoint: Endpoint,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Exception]:
        """
        Called when an error occurs.
        
        Args:
            endpoint: The endpoint that was called
            error: The error that occurred
            context: Additional context
            
        Returns:
            Modified error or None to suppress the error
        """
        return error


class TelemetryMiddleware(Middleware):
    """
    Example middleware for collecting telemetry data.
    
    This can be extended in the future to record patterns for learning.
    """
    
    def __init__(self, record_patterns: bool = False):
        """
        Initialize telemetry middleware.
        
        Args:
            record_patterns: Whether to record patterns for future learning
        """
        self.record_patterns = record_patterns
        self.call_history = []
    
    def before_request(
        self,
        endpoint: Endpoint,
        params: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Record request details."""
        if self.record_patterns:
            self.call_history.append({
                "endpoint": endpoint.path,
                "method": endpoint.method,
                "params": params,
                "timestamp": self._get_timestamp(),
            })
        
        return None, None  # No modification
    
    def after_response(
        self,
        endpoint: Endpoint,
        response: APIResponse,
        context: Optional[Dict[str, Any]] = None,
    ) -> APIResponse:
        """Record response details."""
        if self.record_patterns and self.call_history:
            self.call_history[-1]["response_status"] = response.status_code
            self.call_history[-1]["success"] = response.success
            self.call_history[-1]["duration_ms"] = response.duration_ms
        
        return response  # No modification
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def get_patterns(self) -> list:
        """
        Get recorded patterns for analysis.
        
        Returns:
            List of recorded API calls
        """
        return self.call_history.copy()


class CacheMiddleware(Middleware):
    """
    Example middleware for caching responses.
    
    This is a placeholder for future caching functionality.
    """
    
    def __init__(self, ttl_seconds: int = 300):
        """
        Initialize cache middleware.
        
        Args:
            ttl_seconds: Time-to-live for cache entries in seconds
        """
        self.ttl_seconds = ttl_seconds
        self.cache = {}
    
    def before_request(
        self,
        endpoint: Endpoint,
        params: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Check cache before request."""
        # Future implementation: Check if we have a cached response
        return None, None
    
    def after_response(
        self,
        endpoint: Endpoint,
        response: APIResponse,
        context: Optional[Dict[str, Any]] = None,
    ) -> APIResponse:
        """Cache successful responses."""
        # Future implementation: Cache the response if successful
        return response
