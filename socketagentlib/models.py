"""Data models for Socket Agent client."""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, HttpUrl


class EndpointSchema(BaseModel):
    """Schema definition for an endpoint."""
    
    type: str = Field(default="object")
    properties: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    required: List[str] = Field(default_factory=list)
    additionalProperties: bool = Field(default=False)


class Endpoint(BaseModel):
    """Socket Agent API endpoint definition."""
    
    path: str = Field(..., description="URL path for the endpoint")
    method: str = Field(..., description="HTTP method (GET, POST, etc.)")
    summary: str = Field(..., description="Brief description of the endpoint")
    description: Optional[str] = Field(None, description="Detailed description")
    operationId: Optional[str] = Field(None, description="Unique operation identifier")
    parameters: Optional[List[Dict[str, Any]]] = Field(None, description="Path/query parameters")
    requestBody: Optional[Dict[str, Any]] = Field(None, description="Request body schema")
    responses: Optional[Dict[str, Any]] = Field(None, description="Response schemas")
    tags: Optional[List[str]] = Field(None, description="Endpoint tags/categories")


class AuthConfig(BaseModel):
    """Authentication configuration."""
    
    type: str = Field(default="none", description="Auth type: none, bearer, api_key, basic")
    scheme: Optional[str] = Field(None, description="Auth scheme details")
    header: Optional[str] = Field(None, description="Header name for API key auth")
    description: Optional[str] = Field(None, description="Auth description")


class Descriptor(BaseModel):
    """Socket Agent API descriptor."""
    
    name: str = Field(..., description="API name")
    description: str = Field(..., description="API description")
    version: str = Field(default="1.0.0", description="API version")
    baseUrl: HttpUrl = Field(..., description="Base URL for the API")
    endpoints: List[Endpoint] = Field(..., description="List of API endpoints")
    auth: Optional[AuthConfig] = Field(default_factory=lambda: AuthConfig())
    schemas: Optional[Dict[str, Any]] = Field(None, description="Reusable schemas")
    examples: Optional[List[Union[str, Dict[str, Any]]]] = Field(None, description="Usage examples")
    specVersion: str = Field(default="2025-01-01", description="Socket Agent spec version")
    
    class Config:
        """Pydantic config."""
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "name": "Example API",
                "description": "An example Socket Agent API",
                "version": "1.0.0",
                "baseUrl": "https://api.example.com",
                "endpoints": [
                    {
                        "path": "/users",
                        "method": "GET",
                        "summary": "List all users"
                    }
                ]
            }
        }


class APIResponse(BaseModel):
    """Response from an API call."""
    
    success: bool = Field(..., description="Whether the call succeeded")
    status_code: int = Field(..., description="HTTP status code")
    data: Optional[Any] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if failed")
    headers: Optional[Dict[str, str]] = Field(None, description="Response headers")
    duration_ms: Optional[float] = Field(None, description="Request duration in milliseconds")
