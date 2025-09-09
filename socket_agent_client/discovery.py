"""Descriptor discovery for Socket Agent APIs."""

import json
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx

from .exceptions import DiscoveryError
from .models import Descriptor


class DescriptorFetcher:
    """Fetches and validates Socket Agent descriptors."""
    
    WELL_KNOWN_PATH = "/.well-known/socket-agent"
    DEFAULT_TIMEOUT = 30.0
    
    def __init__(self, timeout: float = DEFAULT_TIMEOUT):
        """
        Initialize descriptor fetcher.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
    
    def fetch(self, base_url: str) -> Descriptor:
        """
        Fetch descriptor from a Socket Agent API.
        
        Args:
            base_url: Base URL of the API
            
        Returns:
            Parsed Descriptor object
            
        Raises:
            DiscoveryError: If fetching or parsing fails
        """
        # Normalize URL
        base_url = self._normalize_url(base_url)
        
        # Build descriptor URL
        descriptor_url = urljoin(base_url, self.WELL_KNOWN_PATH)
        
        try:
            # Fetch descriptor
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    descriptor_url,
                    headers={
                        "Accept": "application/json",
                        "User-Agent": "socket-agent-client/0.1.0"
                    }
                )
                response.raise_for_status()
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise DiscoveryError(
                    f"No Socket Agent descriptor found at {descriptor_url}. "
                    "Ensure the service implements Socket Agent."
                ) from e
            raise DiscoveryError(
                f"HTTP {e.response.status_code} when fetching descriptor"
            ) from e
        except httpx.RequestError as e:
            raise DiscoveryError(f"Failed to fetch descriptor: {e}") from e
        
        # Parse JSON
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            raise DiscoveryError(f"Invalid JSON in descriptor: {e}") from e
        
        # Ensure baseUrl is set
        if "baseUrl" not in data or not data["baseUrl"]:
            data["baseUrl"] = base_url
        
        # Parse and validate descriptor
        try:
            descriptor = Descriptor(**data)
        except Exception as e:
            raise DiscoveryError(f"Invalid descriptor format: {e}") from e
        
        # Additional validation
        self._validate_descriptor(descriptor)
        
        return descriptor
    
    def _normalize_url(self, url: str) -> str:
        """
        Normalize a URL for use as base URL.
        
        Args:
            url: URL to normalize
            
        Returns:
            Normalized URL
            
        Raises:
            DiscoveryError: If URL is invalid
        """
        # Add scheme if missing
        if not url.startswith(("http://", "https://")):
            url = f"http://{url}"
        
        # Parse and validate
        parsed = urlparse(url)
        if not parsed.netloc:
            raise DiscoveryError(f"Invalid URL: {url}")
        
        # Remove trailing slash
        return url.rstrip("/")
    
    def _validate_descriptor(self, descriptor: Descriptor) -> None:
        """
        Validate a descriptor for completeness and correctness.
        
        Args:
            descriptor: Descriptor to validate
            
        Raises:
            DiscoveryError: If validation fails
        """
        # Check required fields
        if not descriptor.name:
            raise DiscoveryError("Descriptor missing required field: name")
        
        if not descriptor.endpoints:
            raise DiscoveryError("Descriptor has no endpoints")
        
        # Validate endpoints
        for endpoint in descriptor.endpoints:
            if not endpoint.path:
                raise DiscoveryError(f"Endpoint missing path: {endpoint}")
            
            if endpoint.method not in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                raise DiscoveryError(
                    f"Invalid HTTP method '{endpoint.method}' for {endpoint.path}"
                )
        
        # Check for duplicate endpoints
        endpoint_keys = [
            f"{ep.method}:{ep.path}" for ep in descriptor.endpoints
        ]
        if len(endpoint_keys) != len(set(endpoint_keys)):
            raise DiscoveryError("Descriptor contains duplicate endpoints")


def fetch_descriptor(base_url: str, timeout: float = 30.0) -> Descriptor:
    """
    Convenience function to fetch a descriptor.
    
    Args:
        base_url: Base URL of the Socket Agent API
        timeout: Request timeout in seconds
        
    Returns:
        Parsed Descriptor object
    """
    fetcher = DescriptorFetcher(timeout=timeout)
    return fetcher.fetch(base_url)
