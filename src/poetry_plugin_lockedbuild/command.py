from __future__ import annotations

import itertools

from typing import TYPE_CHECKING

from cleo.helpers import option
from poetry.console.commands.env_command import EnvCommand

from poetry_plugin_lockedbuild.builder import LockedWheelBuilder


if TYPE_CHECKING:
    from cleo.io.inputs.option import Option


class LockedBuildCommand(EnvCommand):
    name = "lockedbuild"
    description = "Builds a wheel with locked packages from the poetry.lock."

    options: list[Option] = [
        option(
            long_name="with",
            description="The optional dependency groups to include.",
            flag=False,
            multiple=True,
        ),
    ]

    loggers: list[str] = ["poetry.core.masonry.builders.wheel"]

    def handle(self) -> int:
        with_groups = list(itertools.chain.from_iterable([group.split(",") for group in self.option("with")]))

        package = self.poetry.package
        self.line(f"Building <c1>{package.pretty_name}</c1> (<c2>{package.version}</c2>)")

        LockedWheelBuilder(
            self.poetry, env=self.env, locker=self.poetry.locker, executable=self.env.python, with_groups=with_groups
        ).build()

        return 0
