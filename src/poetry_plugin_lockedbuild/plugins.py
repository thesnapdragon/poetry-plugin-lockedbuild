from __future__ import annotations

from typing import TYPE_CHECKING

from poetry.plugins.application_plugin import ApplicationPlugin

from poetry_plugin_lockedbuild.command import LockedBuildCommand


if TYPE_CHECKING:
    from poetry.console.commands.command import Command


class LockedBuildPlugin(ApplicationPlugin):
    @property
    def commands(self) -> list[type[Command]]:
        return [LockedBuildCommand]
