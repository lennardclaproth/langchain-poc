# app/services/errors.py
from __future__ import annotations

from dataclasses import dataclass


class AppError(Exception):
    """Base class for application/service errors."""


@dataclass(slots=True)
class NotFoundError(AppError):
    resource: str
    identifier: str

    def __str__(self) -> str:
        return f"{self.resource} not found ({self.identifier})"


@dataclass(slots=True)
class ConflictError(AppError):
    resource: str
    field: str
    value: str

    def __str__(self) -> str:
        return f"{self.resource} with {self.field}='{self.value}' already exists"


@dataclass(slots=True)
class ValidationError(AppError):
    message: str

    def __str__(self) -> str:
        return self.message
