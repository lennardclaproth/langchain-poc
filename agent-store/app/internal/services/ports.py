# app/services/ports.py
from __future__ import annotations
from typing import Protocol
from app.internal.store.schema import Tool

class ToolSyncPort(Protocol):
    def upsert(self, tool: Tool) -> None: ...
    def remove(self, tool: Tool) -> None: ...
