"""Orbit plugin that registers settings pages on a panel."""

from __future__ import annotations

from typing import Any, Self

from almasix.orbit.panels.hooks import Plugin

from almasix_orbit_settings.config import SettingsPluginConfig


class SettingsPlugin(Plugin):
    """Register :class:`~almasix_orbit_settings.page.SettingsPage` subclasses on a panel."""

    def __init__(self) -> None:
        super().__init__("orbit-settings")
        self.config = SettingsPluginConfig()

    @classmethod
    def make(cls) -> SettingsPlugin:
        return cls()

    def navigation_group(self, name: str) -> Self:
        self.config.navigation_group = str(name)
        return self

    def pages(self, pages: list[type[Any]]) -> Self:
        self.config.pages = list(pages)
        return self

    def cluster(self, cluster: type[Any] | str | None) -> Self:
        self.config.cluster = cluster
        return self

    def without_tenant_resolver(self) -> Self:
        self.config.bind_tenant_resolver = False
        return self

    def register(self, panel: Any) -> None:
        extras = list(self.config.pages)
        if not extras:
            return
        group = self.config.navigation_group
        for page in extras:
            if getattr(page, "navigation_group", None) is None or page.navigation_group == "Settings":
                page.navigation_group = group
            if self.config.cluster is not None and getattr(page, "cluster", None) is None:
                page.cluster = self.config.cluster
        existing = list(panel.get_pages())
        seen = {id(item) for item in existing}
        merged = existing + [item for item in extras if id(item) not in seen]
        panel.pages(merged)

    def boot(self, panel: Any) -> None:
        if not self.config.bind_tenant_resolver:
            return
        tenancy = getattr(panel, "get_tenancy", lambda: None)()
        if tenancy is None or not getattr(tenancy, "is_enabled", lambda: False)():
            return
        from almasix.settings import set_tenant_resolver

        def resolve() -> Any:
            getter = getattr(panel, "get_tenant", None)
            return getter() if callable(getter) else None

        set_tenant_resolver(resolve)
