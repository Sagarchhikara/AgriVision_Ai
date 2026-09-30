"""
backend/services/llm

Pluggable LLM providers behind one interface, so the report service never knows
which vendor produced a report and tests never touch the network.
"""

from backend.services.llm.base import LLMProvider
from backend.services.llm.factory import build_provider
from backend.services.llm.fake import FakeProvider

__all__ = ["LLMProvider", "FakeProvider", "build_provider"]
