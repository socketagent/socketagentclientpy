"""Identity client for socketagent.id integration."""

import time
from typing import Dict, Optional
from urllib.parse import urljoin

import httpx
from pydantic import BaseModel

from .exceptions import AuthenticationError, SocketAgentError


class LoginRequest(BaseModel):
    """Login request data."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response from identity service."""
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str


class RefreshRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str


class UserInfo(BaseModel):
    """User information from identity service."""
    id: int
    username: str
    email: Optional[str] = None
    created_at: str


class TokenManager:
    """Manages access and refresh tokens."""

    def __init__(self):
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.expires_at: Optional[float] = None

    def set_tokens(self, token_response: TokenResponse) -> None:
        """Set tokens from login/refresh response."""
        self.access_token = token_response.access_token
        self.refresh_token = token_response.refresh_token
        self.expires_at = time.time() + token_response.expires_in

    def is_expired(self) -> bool:
        """Check if access token is expired (with 30 second buffer)."""
        if not self.expires_at:
            return True
        return time.time() > (self.expires_at - 30)

    def has_valid_token(self) -> bool:
        """Check if we have a valid access token."""
        return self.access_token is not None and not self.is_expired()

    def get_auth_header(self) -> Optional[Dict[str, str]]:
        """Get authorization header if token is available."""
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return None

    def clear(self) -> None:
        """Clear all tokens."""
        self.access_token = None
        self.refresh_token = None
        self.expires_at = None


class IdentityClient:
    """Client for socketagent.id authentication service."""

    def __init__(self, base_url: str, timeout: float = 10.0):
        """
        Initialize identity client.

        Args:
            base_url: Base URL of socketagent.id service
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.token_manager = TokenManager()

    async def login(self, username: str, password: str) -> TokenResponse:
        """
        Login with username and password.

        Args:
            username: Username
            password: Password

        Returns:
            TokenResponse with access and refresh tokens

        Raises:
            AuthenticationError: If login fails
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    urljoin(self.base_url, "/v1/auth/login"),
                    json=LoginRequest(username=username, password=password).model_dump()
                )

                if response.status_code == 200:
                    token_response = TokenResponse(**response.json())
                    self.token_manager.set_tokens(token_response)
                    return token_response
                elif response.status_code == 401:
                    raise AuthenticationError("Invalid username or password")
                else:
                    raise AuthenticationError(f"Login failed: {response.status_code}")

        except httpx.RequestError as e:
            raise SocketAgentError(f"Identity service connection failed: {e}")

    async def refresh_token(self) -> TokenResponse:
        """
        Refresh access token using refresh token.

        Returns:
            TokenResponse with new access and refresh tokens

        Raises:
            AuthenticationError: If refresh fails
        """
        if not self.token_manager.refresh_token:
            raise AuthenticationError("No refresh token available")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    urljoin(self.base_url, "/v1/auth/refresh"),
                    json=RefreshRequest(refresh_token=self.token_manager.refresh_token).model_dump()
                )

                if response.status_code == 200:
                    token_response = TokenResponse(**response.json())
                    self.token_manager.set_tokens(token_response)
                    return token_response
                elif response.status_code == 401:
                    # Refresh token invalid, clear all tokens
                    self.token_manager.clear()
                    raise AuthenticationError("Refresh token expired")
                else:
                    raise AuthenticationError(f"Token refresh failed: {response.status_code}")

        except httpx.RequestError as e:
            raise SocketAgentError(f"Identity service connection failed: {e}")

    async def logout(self) -> None:
        """
        Logout and revoke refresh token.

        Raises:
            SocketAgentError: If logout request fails
        """
        if not self.token_manager.refresh_token:
            return  # Already logged out

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                await client.post(
                    urljoin(self.base_url, "/v1/auth/logout"),
                    json=RefreshRequest(refresh_token=self.token_manager.refresh_token).model_dump()
                )
                # Don't care about response status for logout
        except httpx.RequestError:
            # Log but don't raise - logout should be best effort
            pass
        finally:
            self.token_manager.clear()

    async def get_user_info(self) -> UserInfo:
        """
        Get current user information.

        Returns:
            UserInfo for the authenticated user

        Raises:
            AuthenticationError: If not authenticated or token invalid
        """
        if not self.token_manager.access_token:
            raise AuthenticationError("Not authenticated")

        try:
            auth_header = self.token_manager.get_auth_header()
            if not auth_header:
                raise AuthenticationError("No valid token available")

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    urljoin(self.base_url, "/v1/me"),
                    headers=auth_header
                )

                if response.status_code == 200:
                    return UserInfo(**response.json())
                elif response.status_code == 401:
                    raise AuthenticationError("Token invalid or expired")
                else:
                    raise SocketAgentError(f"User info request failed: {response.status_code}")

        except httpx.RequestError as e:
            raise SocketAgentError(f"Identity service connection failed: {e}")

    async def ensure_valid_token(self) -> str:
        """
        Ensure we have a valid access token, refreshing if necessary.

        Returns:
            Valid access token

        Raises:
            AuthenticationError: If no tokens available or refresh fails
        """
        if self.token_manager.has_valid_token():
            return self.token_manager.access_token

        if self.token_manager.refresh_token:
            await self.refresh_token()
            if self.token_manager.access_token:
                return self.token_manager.access_token

        raise AuthenticationError("No valid authentication available")

    def get_auth_headers(self) -> Optional[Dict[str, str]]:
        """Get authorization headers if available (sync version)."""
        return self.token_manager.get_auth_header()

    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        return self.token_manager.has_valid_token() or bool(self.token_manager.refresh_token)