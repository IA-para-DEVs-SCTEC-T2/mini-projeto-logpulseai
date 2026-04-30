"""Adaptadores de fonte de log (LogSource)."""

from logpulse.sources.base import LogSource
from logpulse.sources.file_source import FileSource
from logpulse.sources.stdin_source import StdinSource

__all__ = ["LogSource", "FileSource", "StdinSource"]
