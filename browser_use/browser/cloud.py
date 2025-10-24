"""Cloud browser service - PERMANENTLY DISABLED for privacy-focused local-only operation.

All cloud browser functionality has been completely removed to ensure no data
is shared externally. This module is kept only for backward compatibility.
"""

import logging
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class CloudBrowserResponse(BaseModel):
        """Response from cloud browser API - DISABLED."""

        id: str = ''
        status: str = 'disabled'
        liveUrl: str = Field(default='', alias='liveUrl')
        cdpUrl: str = Field(default='', alias='cdpUrl')
        timeoutAt: str = Field(default='', alias='timeoutAt')
        startedAt: str = Field(default='', alias='startedAt')
        finishedAt: str | None = Field(default=None, alias='finishedAt')


class CloudBrowserError(Exception):
        """Exception raised when cloud browser operations fail."""
        pass


class CloudBrowserAuthError(CloudBrowserError):
        """Exception raised when cloud browser authentication fails."""
        pass


class CloudBrowserClient:
        """Cloud browser client - DISABLED, all methods raise errors."""

        def __init__(self, api_base_url: str = ''):
                self.api_base_url = ''
                self.client = None
                self.current_session_id: str | None = None
                logger.warning('Cloud browser service is permanently disabled in this privacy-focused version')

        async def create_browser(self) -> CloudBrowserResponse:
                """Disabled - cloud browsers not available."""
                raise CloudBrowserError(
                        'Cloud browser service is permanently disabled in this privacy-focused version. '
                        'Please use local Chromium browser instead.'
                )

        async def stop_browser(self, session_id: str) -> None:
                """No-op - cloud browsers disabled."""
                pass

        async def get_browser_status(self, session_id: str):
                """No-op - cloud browsers disabled."""
                raise CloudBrowserError('Cloud browser service is permanently disabled')

        async def close(self) -> None:
                """No-op - cloud browsers disabled."""
                pass


async def get_cloud_browser_cdp_url(**kwargs: Any) -> str:
        """Disabled - cloud browsers not available.
        
        Raises:
                CloudBrowserError: Always raises as cloud service is disabled
        """
        raise CloudBrowserError(
                'Cloud browser service is permanently disabled in this privacy-focused version. '
                'Please use local Chromium browser instead (set cloud_browser=False).'
        )


async def cleanup_cloud_client(**kwargs: Any) -> None:
        """No-op - cloud browsers disabled."""
        pass
