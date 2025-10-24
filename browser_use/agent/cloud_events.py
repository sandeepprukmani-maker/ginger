"""Cloud events - PERMANENTLY DISABLED for privacy-focused local-only operation.

All cloud event functionality has been completely removed to ensure no data
is shared externally. This module is kept only for backward compatibility.
"""

from datetime import datetime, timezone

from bubus import BaseEvent
from pydantic import Field
from uuid_extensions import uuid7str

MAX_STRING_LENGTH = 100000
MAX_URL_LENGTH = 100000
MAX_TASK_LENGTH = 100000
MAX_COMMENT_LENGTH = 2000
MAX_FILE_CONTENT_SIZE = 50 * 1024 * 1024


class UpdateAgentTaskEvent(BaseEvent):
        """No-op event - does nothing for privacy."""
        id: str = ''
        user_id: str = Field(default='LOCAL_USER', max_length=255)
        device_id: str | None = Field(default=None, max_length=255)
        stopped: bool | None = None
        paused: bool | None = None
        done_output: str | None = Field(default=None, max_length=MAX_STRING_LENGTH)
        finished_at: datetime | None = None
        agent_state: dict | None = None
        user_feedback_type: str | None = Field(default=None, max_length=10)
        user_comment: str | None = Field(default=None, max_length=MAX_COMMENT_LENGTH)
        gif_url: str | None = Field(default=None, max_length=MAX_URL_LENGTH)

        @classmethod
        def from_agent(cls, agent) -> 'UpdateAgentTaskEvent':
                """No-op method - returns empty event."""
                return cls(
                        id='',
                        user_id='LOCAL_USER',
                        device_id=None,
                        done_output=None,
                        user_feedback_type=None,
                        user_comment=None,
                        gif_url=None
                )


class CreateAgentOutputFileEvent(BaseEvent):
        """No-op event - does nothing for privacy."""
        id: str = Field(default_factory=uuid7str)
        user_id: str = Field(default='LOCAL_USER', max_length=255)
        device_id: str | None = Field(default=None, max_length=255)
        task_id: str = ''
        file_name: str = Field(default='', max_length=255)
        file_content: str | None = None
        content_type: str | None = Field(default=None, max_length=100)
        created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

        @classmethod
        async def from_agent_and_file(cls, agent, output_path: str) -> 'CreateAgentOutputFileEvent':
                """No-op method - returns empty event."""
                return cls(
                        task_id='',
                        user_id='LOCAL_USER',
                        device_id=None,
                        content_type=None
                )


class CreateAgentStepEvent(BaseEvent):
        """No-op event - does nothing for privacy."""
        id: str = Field(default_factory=uuid7str)
        user_id: str = Field(default='LOCAL_USER', max_length=255)
        device_id: str | None = Field(default=None, max_length=255)
        created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
        agent_task_id: str = ''
        step: int = 0
        evaluation_previous_goal: str = Field(default='', max_length=MAX_STRING_LENGTH)
        memory: str = Field(default='', max_length=MAX_STRING_LENGTH)
        next_goal: str = Field(default='', max_length=MAX_STRING_LENGTH)
        thinking: str = Field(default='', max_length=MAX_STRING_LENGTH)
        actions: list = Field(default_factory=list)
        result: str = Field(default='', max_length=MAX_STRING_LENGTH)
        url: str = Field(default='', max_length=MAX_URL_LENGTH)
        screenshot: str | None = None

        @classmethod
        def from_agent_and_step(cls, agent, step_info, screenshot_base64: str | None = None) -> 'CreateAgentStepEvent':
                """No-op method - returns empty event."""
                return cls(
                        agent_task_id='',
                        user_id='LOCAL_USER',
                        device_id=None
                )


class CreateAgentSessionEvent(BaseEvent):
        """No-op event - does nothing for privacy."""
        id: str = Field(default_factory=uuid7str)
        user_id: str = Field(default='LOCAL_USER', max_length=255)
        device_id: str | None = Field(default=None, max_length=255)
        created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
        agent_task_id: str = ''
        browser_session_id: str = ''

        @classmethod
        def from_agent_and_browser_session(cls, agent, browser_session) -> 'CreateAgentSessionEvent':
                """No-op method - returns empty event."""
                return cls(
                        agent_task_id='',
                        browser_session_id='',
                        user_id='LOCAL_USER',
                        device_id=None
                )


class CreateAgentTaskEvent(BaseEvent):
        """No-op event - does nothing for privacy."""
        id: str = Field(default_factory=uuid7str)
        user_id: str = Field(default='LOCAL_USER', max_length=255)
        device_id: str | None = Field(default=None, max_length=255)
        created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
        task: str = Field(default='', max_length=MAX_TASK_LENGTH)
        started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
        max_steps: int = 0
        llm_model: str = Field(default='', max_length=100)
        llm_provider: str = Field(default='', max_length=100)
        agent_type: str | None = Field(default=None, max_length=50)

        @classmethod
        def from_agent(cls, agent) -> 'CreateAgentTaskEvent':
                """No-op method - returns empty event."""
                return cls(
                        id='',
                        user_id='LOCAL_USER',
                        device_id=None,
                        agent_type=None
                )
