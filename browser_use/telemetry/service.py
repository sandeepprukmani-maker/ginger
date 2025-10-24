"""Telemetry service - PERMANENTLY DISABLED for privacy-focused local-only operation.

All telemetry functionality has been completely removed to ensure no data
is shared externally. This module is kept only for backward compatibility.
"""

import logging

from browser_use.telemetry.views import BaseTelemetryEvent
from browser_use.utils import singleton

logger = logging.getLogger(__name__)


@singleton
class ProductTelemetry:
        """
        Telemetry service - PERMANENTLY DISABLED.
        
        This is a no-op service that does nothing.
        All data collection has been removed for privacy.
        """

        def __init__(self) -> None:
                self._posthog_client = None
                logger.debug('Telemetry permanently disabled - local-only privacy mode')

        def capture(self, event: BaseTelemetryEvent) -> None:
                """No-op capture method - does nothing."""
                pass

        def flush(self) -> None:
                """No-op flush method - does nothing."""
                pass

        @property
        def user_id(self) -> str:
                """Returns a constant string - no user tracking."""
                return 'LOCAL_USER'
