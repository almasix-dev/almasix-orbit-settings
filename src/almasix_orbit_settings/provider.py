"""Service provider — registers smith commands."""

from __future__ import annotations

from almasix.providers import ServiceProvider


class OrbitSettingsProvider(ServiceProvider):
    def register(self) -> None:
        return None

    def boot(self) -> None:
        from almasix_orbit_settings.commands import MakeOrbitSettingsPageCommand

        self.commands([MakeOrbitSettingsPageCommand])
