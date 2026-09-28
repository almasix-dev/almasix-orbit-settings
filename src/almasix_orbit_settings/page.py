"""Settings page — Orbit Page bound to an Almasix Settings class."""

from __future__ import annotations

from typing import Any, ClassVar

from almasix.orbit.forms import Form
from almasix.orbit.panels.page import Page
from almasix.settings import Settings


class SettingsPage(Page):
    """Panel page that edits one :class:`~almasix.settings.Settings` class."""

    navigation_icon: ClassVar[str] = "heroicon-o-cog-6-tooth"
    navigation_group: ClassVar[str | None] = "Settings"
    settings: ClassVar[type[Settings] | None] = None
    #: When None, follows ``settings.is_tenant_scoped()``.
    is_scoped_to_tenant: ClassVar[bool | None] = None

    @classmethod
    def get_settings_class(cls) -> type[Settings]:
        if cls.settings is None:
            raise RuntimeError(f"{cls.__name__}.settings must point at a Settings subclass")
        return cls.settings

    @classmethod
    def settings_are_tenant_scoped(cls) -> bool:
        if cls.is_scoped_to_tenant is not None:
            return bool(cls.is_scoped_to_tenant)
        return cls.get_settings_class().is_tenant_scoped()

    @classmethod
    def form(cls, form: Form) -> Form:
        return form

    @classmethod
    def get_form(cls) -> Form:
        return cls.form(Form.make())

    @classmethod
    def can_access(cls, user: Any = None) -> bool:
        return True

    @classmethod
    def can_edit(cls, user: Any = None) -> bool:
        return True

    @classmethod
    def mutate_form_data_before_fill(cls, data: dict[str, Any]) -> dict[str, Any]:
        return data

    @classmethod
    def mutate_form_data_before_save(cls, data: dict[str, Any]) -> dict[str, Any]:
        return data

    @classmethod
    def after_save(cls, settings: Settings, data: dict[str, Any]) -> None:
        return None

    @classmethod
    def get_conduit_host(cls) -> type[Any] | None:
        from almasix_orbit_settings.host import SettingsFormHost

        return SettingsFormHost.bind(page=cls)

    @classmethod
    def render(cls, **ctx: Any) -> str:
        # Static fallback when Conduit is unavailable.
        return (
            f'<div class="or-page"><h1 class="or-page-title">{cls.get_title()}</h1>'
            '<p class="or-muted">Settings require a Conduit-backed panel mount.</p></div>'
        )
