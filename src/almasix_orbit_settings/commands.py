"""Smith command for Orbit settings pages."""

from __future__ import annotations

import re
from pathlib import Path

from almasix.console.command import Command


def _snake(name: str) -> str:
    text = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", text).lower()


def _studly(name: str) -> str:
    return "".join(part.capitalize() for part in re.split(r"[_\-\s]+", name) if part)


class MakeOrbitSettingsPageCommand(Command):
    signature = (
        "make:orbit-settings-page {name : Page class (e.g. ManageGeneralSettings)}"
        " {--settings= : Settings class name}"
        " {--panel=app : Panel id}"
        " {--tenant-scoped : Mark the Settings class tenant-scoped}"
    )
    description = "Create an Orbit SettingsPage (and optional Settings class stub)"

    def handle(self) -> int:
        raw = str(self.argument("name") or "").strip()
        if not raw:
            self.error("name is required")
            return self.FAILURE
        page_name = _studly(raw)
        if not page_name.endswith("Page") and not page_name.startswith("Manage"):
            page_name = f"Manage{page_name}"
        settings_opt = self.option("settings")
        if settings_opt:
            settings_name = _studly(str(settings_opt))
        else:
            settings_name = page_name.replace("Manage", "") + "Settings"
        if not settings_name.endswith("Settings"):
            settings_name = f"{settings_name}Settings"
        panel_id = str(self.option("panel") or "app").strip() or "app"
        tenant_scoped = bool(self.option("tenant-scoped"))
        pages_dir = Path(self.app.base_path) / "app" / "orbit" / panel_id / "pages"
        pages_dir.mkdir(parents=True, exist_ok=True)
        page_path = pages_dir / f"{_snake(page_name)}.py"
        settings_dir = Path(self.app.base_path) / "app" / "settings"
        settings_dir.mkdir(parents=True, exist_ok=True)
        settings_path = settings_dir / f"{_snake(settings_name)}.py"
        group = _snake(settings_name.removesuffix("Settings"))
        label = group.replace("_", " ").title()
        slug = _snake(page_name).replace("_", "-")
        if not settings_path.exists():
            scoped_line = "    tenant_scoped = True\n\n" if tenant_scoped else ""
            settings_path.write_text(
                (
                    '"""Application settings."""\n\n'
                    "from __future__ import annotations\n\n"
                    "from almasix.settings import Settings\n\n\n"
                    f"class {settings_name}(Settings):\n"
                    f"{scoped_line}"
                    "    site_name: str\n\n"
                    "    @classmethod\n"
                    "    def group(cls) -> str:\n"
                    f'        return "{group}"\n'
                ),
                encoding="utf-8",
            )
            self.success(f"Created {settings_path}")
        if page_path.exists():
            self.warn(f"Already exists: {page_path}")
            return self.SUCCESS
        page_path.write_text(
            (
                '"""Orbit settings page."""\n\n'
                "from __future__ import annotations\n\n"
                "from almasix.orbit.forms import Form, TextInput\n"
                "from almasix_orbit_settings import SettingsPage\n\n"
                f"from app.settings.{_snake(settings_name)} import {settings_name}\n\n\n"
                f"class {page_name}(SettingsPage):\n"
                f"    settings = {settings_name}\n"
                f'    title = "{label}"\n'
                f'    navigation_label = "{label}"\n'
                f'    slug = "{slug}"\n\n'
                "    @classmethod\n"
                "    def form(cls, form: Form) -> Form:\n"
                "        return form.schema([\n"
                '            TextInput.make("site_name").label("Site name").required(),\n'
                "        ])\n"
            ),
            encoding="utf-8",
        )
        self.success(f"Created {page_path}")
        self.info(f"Register with SettingsPlugin.make().pages([{page_name}])")
        return self.SUCCESS
