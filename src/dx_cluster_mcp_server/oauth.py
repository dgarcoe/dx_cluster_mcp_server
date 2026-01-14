"""OAuth authentication for the DX Cluster MCP Server."""

import os
import secrets
from typing import Optional
from starlette.requests import Request
from starlette.responses import JSONResponse


class OAuthConfig:
    """OAuth configuration for the MCP server."""

    def __init__(self):
        """Initialize OAuth configuration from environment variables."""
        self.enabled = os.getenv("OAUTH_ENABLED", "false").lower() == "true"
        self.client_id = os.getenv("OAUTH_CLIENT_ID", "")
        self.client_secret = os.getenv("OAUTH_CLIENT_SECRET", "")

        # Generate a random client secret if not provided and OAuth is enabled
        if self.enabled and not self.client_secret:
            self.client_secret = secrets.token_urlsafe(32)
            print(f"⚠ Generated random client secret: {self.client_secret}")
            print("⚠ Set OAUTH_CLIENT_SECRET in your environment to use a persistent secret")

    def validate(self) -> bool:
        """Validate OAuth configuration.

        Returns:
            True if configuration is valid, False otherwise.
        """
        if not self.enabled:
            return True

        if not self.client_id:
            print("⚠ OAUTH_CLIENT_ID is required when OAUTH_ENABLED=true")
            return False

        if not self.client_secret:
            print("⚠ OAUTH_CLIENT_SECRET is required when OAUTH_ENABLED=true")
            return False

        return True


def extract_bearer_token(request: Request) -> Optional[str]:
    """Extract bearer token from request.

    Args:
        request: The Starlette request object.

    Returns:
        The bearer token if present, None otherwise.
    """
    authorization = request.headers.get("Authorization", "")

    if authorization.startswith("Bearer "):
        return authorization[7:]  # Remove "Bearer " prefix

    return None


async def validate_oauth_middleware(request: Request, call_next, oauth_config: OAuthConfig):
    """Middleware to validate OAuth tokens.

    Args:
        request: The incoming request.
        call_next: The next middleware or handler.
        oauth_config: OAuth configuration.

    Returns:
        The response from the next handler or an error response.
    """
    # Skip authentication for health check endpoint
    if request.url.path == "/health":
        return await call_next(request)

    # If OAuth is disabled, allow all requests
    if not oauth_config.enabled:
        return await call_next(request)

    # Extract and validate bearer token
    token = extract_bearer_token(request)

    if not token:
        return JSONResponse(
            status_code=401,
            content={
                "error": "unauthorized",
                "message": "Missing or invalid Authorization header. "
                          "Expected format: Authorization: Bearer <client_secret>"
            }
        )

    # Validate token matches client secret
    if token != oauth_config.client_secret:
        return JSONResponse(
            status_code=403,
            content={
                "error": "forbidden",
                "message": "Invalid authentication credentials"
            }
        )

    # Token is valid, proceed with request
    return await call_next(request)
