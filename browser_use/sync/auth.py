"""Cloud authentication - PERMANENTLY DISABLED for privacy-focused local-only operation.

All cloud authentication functionality has been completely removed to ensure no data
is shared externally. This module is kept only for backward compatibility.
"""

import json
import os
from datetime import datetime

from pydantic import BaseModel
from uuid_extensions import uuid7str

from browser_use.config import CONFIG

# Temporary user ID (not used but kept for compatibility)
TEMP_USER_ID = '99999999-9999-9999-9999-999999999999'


def get_or_create_device_id() -> str:
        """Get or create a local device ID (stays local, never sent anywhere)."""
        device_id_path = CONFIG.BROWSER_USE_CONFIG_DIR / 'device_id'

        # Try to read existing device ID
        if device_id_path.exists():
                try:
                        device_id = device_id_path.read_text().strip()
                        if device_id:
                                return device_id
                except Exception:
                        pass

        # Create new device ID
        device_id = uuid7str()

        # Ensure config directory exists
        CONFIG.BROWSER_USE_CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        # Write device ID to file (local only)
        device_id_path.write_text(device_id)

        return device_id


class CloudAuthConfig(BaseModel):
        """Cloud auth config - DISABLED, returns empty config."""

        api_token: str | None = None
        user_id: str | None = None
        authorized_at: datetime | None = None

        @classmethod
        def load_from_file(cls) -> 'CloudAuthConfig':
                """Returns empty config - no cloud auth."""
                return cls()

        def save_to_file(self) -> None:
                """No-op - cloud auth disabled."""
                pass


class DeviceAuthClient:
        """Device auth client - DISABLED, all methods are no-ops."""

        def __init__(self, base_url: str | None = None, http_client=None):
                self.base_url = ''
                self.client_id = 'local'
                self.scope = ''
                self.http_client = None
                self.temp_user_id = TEMP_USER_ID
                self.device_id = get_or_create_device_id()
                self.auth_config = CloudAuthConfig()

        @property
        def is_authenticated(self) -> bool:
                """Always returns False - no cloud auth."""
                return False

        @property
        def api_token(self) -> str | None:
                """Always returns None - no cloud auth."""
                return None

        @property
        def user_id(self) -> str:
                """Returns local user ID."""
                return 'LOCAL_USER'

        async def start_device_authorization(self, agent_session_id: str | None = None):
                """No-op - cloud auth disabled."""
                pass

        async def poll_for_token(self, device_code: str, interval: int = 5):
                """No-op - cloud auth disabled."""
                pass

        async def exchange_device_code(self, device_code: str):
                """No-op - cloud auth disabled."""
                pass

        def logout(self) -> None:
                """No-op - cloud auth disabled."""
                pass

        async def close(self) -> None:
                """No-op - cloud auth disabled."""
                pass
