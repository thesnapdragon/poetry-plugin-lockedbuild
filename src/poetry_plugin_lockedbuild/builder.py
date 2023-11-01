from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Sequence

from cleo.io.null_io import NullIO
from poetry.core.masonry.builders.wheel import WheelBuilder
from poetry.core.packages.dependency_group import MAIN_GROUP
from poetry.puzzle import Solver
from poetry.repositories import Repository
from poetry.repositories import RepositoryPool


if TYPE_CHECKING:
    from pathlib import Path

    from poetry.core.packages.package import Package
    from poetry.core.poetry import Poetry
    from poetry.packages import Locker
    from poetry.utils.env import Env


class LockedWheelBuilder(WheelBuilder):
    def __init__(
        self,
        poetry: Poetry,
        env: Env,
        locker: Locker,
        executable: Path | None = None,
        with_groups: Sequence[str] = (),
    ) -> None:
        super().__init__(poetry, executable=executable)

        self._poetry = poetry
        self._env = env
        self._locker = locker
        self._with_groups = list(with_groups)

    def prepare_metadata(self, metadata_directory: Path) -> Path:
        in_extras = {dependency.pretty_name: dependency.in_extras for dependency in self._poetry.package.requires}

        self._meta.requires_dist = []
        for package in self._resolved_packages:
            name = package.pretty_name

            package.python_versions = "*"

            dependency = package.to_dependency()
            if name in in_extras:
                dependency.in_extras.extend(in_extras[name])

            self._meta.requires_dist.append(dependency.to_pep_508())

        return super().prepare_metadata(metadata_directory)

    @property
    def _resolved_packages(self) -> list[Package]:
        repository = Repository(name="temporary-repository")

        for package in self._locker.locked_repository().packages:
            if not package.is_direct_origin() and not repository.has_package(package):
                repository.add_package(package)

        solver = Solver(
            package=self._poetry.package.with_dependency_groups(groups={MAIN_GROUP, *self._with_groups}, only=True),
            pool=RepositoryPool(repositories=[repository]),
            installed=[],
            locked=[],
            io=NullIO(),
        )
        solver.provider.load_deferred(False)

        with solver.use_environment(self._env):
            operations = solver.solve().calculate_operations()

        return [operation.package for operation in operations]
