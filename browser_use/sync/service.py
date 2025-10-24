"""Cloud sync service - PERMANENTLY DISABLED for privacy-focused local-only operation.

All cloud sync functionality has been completely removed to ensure no data
is shared externally. This module is kept only for backward compatibility.
"""

import logging

from bubus import BaseEvent

from browser_use.config import CONFIG
from browser_use.sync.auth import DeviceAuthClient

logger = logging.getLogger(__name__)


class CloudSync:
        """Cloud sync service - DISABLED, all methods are no-ops."""

        def __init__(self, base_url: str | None = None, allow_session_events_for_auth: bool = False):
                self.base_url = ''
                self.auth_client = DeviceAuthClient()
                self.session_id: str | None = None
                self.allow_session_events_for_auth = False
                self.auth_flow_active = False
                self.enabled = False  # Always disabled

        async def handle_event(self, event: BaseEvent) -> None:
                """No-op - cloud sync disabled."""
                pass

        async def _send_event(self, event: BaseEvent) -> None:
                """No-op - cloud sync disabled."""
                pass

        async def close(self) -> None:
                """No-op - cloud sync disabled."""
                pass
