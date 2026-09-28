"""Tests for almasix-orbit-settings."""

from __future__ import annotations

from almasix.encryption.encrypter import Encrypter
from almasix.encryption.facade import Crypt
from almasix.orbit.forms import Form, TextInput, Toggle
from almasix.orbit.panels.panel import Panel
from almasix.settings import (
    Settings,
    SettingsMigrator,
    bootstrap_default_repositories,
    clear_current_tenant,
    register_repository,
    set_current_tenant,
    set_default_repository,
    set_tenant_resolver,
)
from almasix.settings.repositories.memory import MemorySettingsRepository

from almasix_orbit_settings import SettingsPage, SettingsPlugin
from almasix_orbit_settings.host import SettingsFormHost


class GeneralSettings(Settings):
    site_name: str
    site_active: bool

    @classmethod
    def group(cls) -> str:
        return "general"


class TeamBrandingSettings(Settings):
    tenant_scoped = True
    brand_name: str

    @classmethod
    def group(cls) -> str:
        return "branding"


class ManageGeneralSettings(SettingsPage):
    settings = GeneralSettings
    title = "General"
    slug = "general-settings"

    @classmethod
    def form(cls, form: Form) -> Form:
        return form.schema(
            [
                TextInput.make("site_name").required(),
                Toggle.make("site_active"),
            ]
        )


class ManageBrandingSettings(SettingsPage):
    settings = TeamBrandingSettings
    title = "Branding"
    slug = "branding-settings"

    @classmethod
    def form(cls, form: Form) -> Form:
        return form.schema([TextInput.make("brand_name").required()])


def _seed() -> None:
    bootstrap_default_repositories()
    mem = MemorySettingsRepository()
    register_repository("memory", mem)
    set_default_repository("memory")
    clear_current_tenant()
    set_tenant_resolver(None)
    Crypt.set_encrypter(Encrypter("orbit-settings-test"))
    SettingsMigrator().in_group(
        "general",
        lambda b: (b.add("site_name", "Orbit"), b.add("site_active", True)),
    )
    SettingsMigrator().in_group(
        "branding",
        lambda b: b.add("brand_name", "Global Brand"),
    )


def test_plugin_registers_pages_and_tenant_resolver() -> None:
    _seed()
    panel = Panel.make("app").path("/app")
    plugin = (
        SettingsPlugin.make()
        .navigation_group("Configuration")
        .pages([ManageGeneralSettings, ManageBrandingSettings])
    )
    panel.plugin(plugin)
    panel.run_plugins()
    assert ManageGeneralSettings in panel.get_pages()
    assert ManageGeneralSettings.navigation_group == "Configuration"
    assert ManageGeneralSettings.get_conduit_host() is not None


def test_settings_form_host_load_and_save() -> None:
    _seed()
    panel = Panel.make("app").path("/app")
    host_cls = SettingsFormHost.bind(page=ManageGeneralSettings, panel=panel)
    host = host_cls()
    host.mount()
    assert host.data["site_name"] == "Orbit"
    host.data["site_name"] = "Acme"
    host.data["site_active"] = False
    # Bypass validation helpers that need a full Conduit bag.
    host._validate_or_fail = lambda *_a, **_k: True  # type: ignore[method-assign]
    host.save()
    assert host.saved is True
    assert GeneralSettings.load().site_name == "Acme"
    html = host.render()
    assert "Settings saved" in html
    assert "or-page-settings" in html


def test_tenant_scoped_host_uses_panel_tenant() -> None:
    _seed()

    class FakePanel:
        id = "app"

        def __init__(self) -> None:
            self._tenant = type("T", (), {"id": "acme"})()

        def get_tenant(self):
            return self._tenant

        def get_tenancy(self):
            return type("Ten", (), {"is_enabled": lambda self: True})()

    panel = FakePanel()
    plugin = SettingsPlugin.make().pages([ManageBrandingSettings])
    plugin.boot(panel)
    host_cls = SettingsFormHost.bind(page=ManageBrandingSettings, panel=panel)
    host = host_cls()
    host.mount()
    assert host.data["brand_name"] == "Global Brand"
    host.data["brand_name"] = "Acme Brand"
    host._validate_or_fail = lambda *_a, **_k: True  # type: ignore[method-assign]
    host.save()
    set_current_tenant("acme")
    assert TeamBrandingSettings.load().brand_name == "Acme Brand"
    set_current_tenant("beta")
    assert TeamBrandingSettings.load().brand_name == "Global Brand"


def test_readonly_when_cannot_edit() -> None:
    _seed()

    class ReadOnlyPage(ManageGeneralSettings):
        @classmethod
        def can_edit(cls, user=None) -> bool:
            return False

    panel = Panel.make("app").path("/app")
    host_cls = SettingsFormHost.bind(page=ReadOnlyPage, panel=panel)
    host = host_cls()
    host.mount()
    host._validate_or_fail = lambda *_a, **_k: True  # type: ignore[method-assign]
    host.save()
    assert host.error
    assert GeneralSettings.load().site_name == "Orbit"
