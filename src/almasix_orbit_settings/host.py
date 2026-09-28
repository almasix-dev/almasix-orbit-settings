"""Conduit host that loads and saves a Settings class through a form."""

from __future__ import annotations

from typing import Any, ClassVar

from almasix.orbit.panels.conduit.hosts import FormDataMutations, OrbitPageHost
from almasix.orbit.support.conduit_attrs import conduit_attr
from almasix.orbit.support.html import e
from almasix.settings import Settings, set_current_tenant
from almasix.settings.tenant import clear_current_tenant


class SettingsFormHost(FormDataMutations, OrbitPageHost):
    """Interactive settings editor."""

    data: dict[str, Any] = {}
    select_search: dict[str, str] = {}
    morph_search: dict[str, str] = {}
    table_select: dict[str, Any] = {}
    error: str = ""
    saved: bool = False
    _page_cls: ClassVar[type[Any] | None] = None
    _panel: ClassVar[Any] = None
    _form_factory: ClassVar[Any] = None
    _settings_cls: ClassVar[type[Settings] | None] = None
    _title: ClassVar[str] = "Settings"
    _readonly: ClassVar[bool] = False

    @classmethod
    def bind(cls, *, page: type[Any], panel: Any = None) -> type[SettingsFormHost]:
        settings_cls = page.get_settings_class()

        class Bound(SettingsFormHost):
            pass

        Bound._page_cls = page
        Bound._panel = panel
        Bound._settings_cls = settings_cls
        Bound._title = page.get_title()
        Bound._form_factory = page.get_form
        panel_id = getattr(panel, "id", None) or "admin"
        slug = page.get_slug() if hasattr(page, "get_slug") else page.__name__.lower()
        Bound._conduit_name = f"orbit.{panel_id}.settings.{slug}"
        return Bound

    def _apply_tenant(self) -> None:
        page = type(self)._page_cls
        if page is None or not page.settings_are_tenant_scoped():
            clear_current_tenant()
            return
        panel = type(self)._panel or self.get_panel()
        tenant = None
        if panel is not None:
            getter = getattr(panel, "get_tenant", None)
            if callable(getter):
                tenant = getter()
        set_current_tenant(tenant)

    def get_panel(self) -> Any:
        return type(self)._panel

    def mount(self, **kwargs: Any) -> None:
        self.error = ""
        self.saved = False
        self._apply_tenant()
        page = type(self)._page_cls
        settings_cls = type(self)._settings_cls
        if page is None or settings_cls is None:
            return
        user = kwargs.get("user")
        if hasattr(page, "can_access") and not page.can_access(user):
            self.error = "You cannot view these settings."
            self.data = {}
            return
        type(self)._readonly = not page.can_edit(user)
        settings = settings_cls.load()
        data = page.mutate_form_data_before_fill(settings.to_dict())
        self.data = dict(data)

    def save(self) -> None:
        self.reset_skip_render()
        self.error = ""
        self.saved = False
        page = type(self)._page_cls
        settings_cls = type(self)._settings_cls
        if page is None or settings_cls is None:
            return
        if type(self)._readonly:
            self.error = "You cannot edit these settings."
            return
        if not self._validate_or_fail("edit"):
            return
        self._apply_tenant()
        data = page.mutate_form_data_before_save(dict(self.data))
        settings = settings_cls.load()
        settings.fill(data, respect_locked=True)
        settings.save()
        page.after_save(settings, data)
        self.data = settings.to_dict()
        self.saved = True
        self.dispatch("orbit-settings-saved", data=dict(self.data))

    def render(self) -> str:
        title = e(type(self)._title)
        if self.error and not self.data:
            return (
                f'<div class="or-page or-page-settings"><h1 class="or-page-title">{title}</h1>'
                f'<p class="or-danger">{e(self.error)}</p></div>'
            )
        factory = type(self)._form_factory
        form = factory() if callable(factory) else None
        if form is None:
            return f'<div class="or-page"><h1 class="or-page-title">{title}</h1></div>'
        if type(self)._readonly and hasattr(form, "readonly"):
            form.readonly()
        notice = ""
        if self.saved:
            notice = '<p class="or-success">Settings saved.</p>'
        elif self.error:
            notice = f'<p class="or-danger">{e(self.error)}</p>'
        locked = set()
        settings_cls = type(self)._settings_cls
        if settings_cls is not None:
            from almasix.settings import get_repository

            try:
                locked = set(
                    get_repository(settings_cls.repository()).get_locked_properties(
                        settings_cls.group()
                    )
                )
            except Exception:
                locked = set()
        actions = ""
        if not type(self)._readonly:
            actions = (
                '<div class="or-form-actions">'
                '<button type="submit" class="or-btn or-btn-primary">Save</button>'
                "</div>"
            )
        body = form.render(
            self.data,
            select_search=dict(self.select_search or {}),
            morph_search=dict(self.morph_search or {}),
            table_select=dict(self.table_select or {}),
            form_errors=self.get_error_bag(),
            locked_fields=locked,
        )
        return (
            f'<div class="or-page or-page-settings" data-settings="{e(settings_cls.group() if settings_cls else "")}">'
            f'<header class="or-page-header"><h1 class="or-page-title">{title}</h1></header>'
            f"{notice}"
            f'<form class="or-form"{conduit_attr("submit", "save")} '
            f"x-data "
            f'@keydown.ctrl.s.window.prevent="$el.requestSubmit()" '
            f'@keydown.meta.s.window.prevent="$el.requestSubmit()">'
            f"{body}{actions}</form></div>"
        )
