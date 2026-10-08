"""Canonical, validated telemetry contracts used by API, replay and demo paths."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from ipaddress import ip_address
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class OperatingMode(str, Enum):
    DEMO = "DEMO"
    REPLAY = "REPLAY"
    LIVE = "LIVE"


class TelemetryEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"evt-{uuid4().hex}", min_length=8, max_length=128)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_ip: str
    destination_ip: str
    source_port: int = Field(default=0, ge=0, le=65535)
    destination_port: int = Field(default=0, ge=0, le=65535)
    protocol: str = Field(default="unknown", max_length=32)
    bytes: int = Field(default=0, ge=0)
    packets: int = Field(default=0, ge=0)
    duration: float = Field(default=0.0, ge=0.0)
    direction: str = Field(default="unknown", max_length=32)
    device_id: str | None = Field(default=None, max_length=128)
    user_id: str | None = Field(default=None, max_length=128)
    hostname: str | None = Field(default=None, max_length=255)
    event_type: str = Field(default="network_flow", max_length=64)
    label: str | None = Field(default=None, max_length=64)
    attack_stage: str | None = Field(default=None, max_length=64)
    mitre_technique: str | None = Field(default=None, max_length=32)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("source_ip", "destination_ip")
    @classmethod
    def valid_ip(cls, value: str) -> str:
        return str(ip_address(value))

    @field_validator("timestamp")
    @classmethod
    def timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("timestamp must include a timezone")
        return value.astimezone(timezone.utc)
