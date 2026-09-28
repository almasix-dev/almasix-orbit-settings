"""Orbit Settings plugin configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SettingsPluginConfig:
    navigation_group: str = "Settings"
    pages: list[type[Any]] = field(default_factory=list)
    cluster: type[Any] | str | None = None
    bind_tenant_resolver: bool = True
