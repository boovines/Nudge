"""
Composio MCP client setup and initialization.
"""

import os
from typing import Optional
from config_loader import Config

class ComposioClient:
    """Wrapper for Composio MCP client."""
    
    def __init__(self):
        self.config = Config()
        self.client = None
        self.toolset = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Composio client."""
        try:
            # Try importing Composio - adjust import based on actual SDK
            try:
                from composio.client import ComposioToolSet
            except ImportError:
                try:
                    from composio import ComposioToolSet
                except ImportError:
                    raise ImportError(
                        "Composio package not installed. Install with: pip install composio-core"
                    )
        except ImportError as e:
            raise ImportError(
                "Composio package not installed. Install with: pip install composio-core"
            ) from e
        
        if not self.config.composio_api_key:
            raise ValueError(
                "COMPOSIO_API_KEY not found in environment variables. "
                "Set it in your .env file."
            )
        
        # Initialize Composio client
        # Note: Actual implementation may vary based on Composio SDK version
        # Adjust the initialization method based on actual Composio API documentation
        try:
            # Try different initialization patterns based on Composio SDK version
            self.toolset = ComposioToolSet(api_key=self.config.composio_api_key)
            self.client = self.toolset
        except Exception as e:
            # If initialization fails, try alternative method
            try:
                self.toolset = ComposioToolSet()
                self.toolset.api_key = self.config.composio_api_key
                self.client = self.toolset
            except Exception as e2:
                raise RuntimeError(
                    f"Failed to initialize Composio client: {str(e)}. "
                    f"Alternative method also failed: {str(e2)}. "
                    "Please check Composio SDK documentation for correct initialization."
                ) from e2
    
    def get_client(self):
        """Get the Composio client instance."""
        if self.client is None:
            raise RuntimeError("Composio client not initialized")
        return self.client
    
    def get_toolset(self):
        """Get the Composio toolset."""
        if self.toolset is None:
            raise RuntimeError("Composio toolset not initialized")
        return self.toolset

