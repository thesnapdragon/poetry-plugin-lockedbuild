from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import Protocol

from poetry.console.application import Application
from poetry.core.packages.package import Package
from poetry.core.packages.utils.link import Link
from poetry.factory import Factory
from poetry.packages import Locker
from poetry.repositories import Repository
from poetry.repositories.exceptions import PackageNotFound


if TYPE_CHECKING:
    from pathlib import Path

    from cleo.testers.command_tester import CommandTester
    from poetry.core.constraints.version import Version
    from poetry.core.packages.dependency import Dependency
    from poetry.installation import Installer
    from poetry.installation.executor import Executor
    from poetry.poetry import Poetry
    from poetry.utils.env import Env
    from tomlkit.toml_document import TOMLDocument


class FixtureCopier(Protocol):
    def __call__(self, relative_path: str, target: Path | None = None) -> Path:
        ...


class FixtureDirGetter(Protocol):
    def __call__(self, name: str) -> Path:
        ...


class CommandTesterFactory(Protocol):
    def __call__(
        self,
        command: str,
        poetry: Poetry | None = None,
        installer: Installer | None = None,
        executor: Executor | None = None,
        environment: Env | None = None,
    ) -> CommandTester:
        ...


class ProjectFactory(Protocol):
    def __call__(
        self,
        name: str,
        dependencies: dict[str, str] | None = None,
        dev_dependencies: dict[str, str] | None = None,
        pyproject_content: str | None = None,
        poetry_lock_content: str | None = None,
        install_deps: bool = True,
    ) -> Poetry:
        ...


class PoetryTestApplication(Application):
    def __init__(self, poetry: Poetry) -> None:
        super().__init__()
        self._poetry = poetry

    def reset_poetry(self) -> None:
        poetry = self._poetry
        assert poetry
        self._poetry = Factory().create_poetry(poetry.file.path.parent)
        self._poetry.set_pool(poetry.pool)
        self._poetry.set_config(poetry.config)
        self._poetry.set_locker(TestLocker(poetry.locker.lock, self._poetry.local_config))


class TestLocker(Locker):
    def __init__(self, lock: Path, local_config: dict[str, Any]) -> None:
        super().__init__(lock, local_config)
        self._locked = False
        self._write = False
        self._contains_credential = False

    def write(self, write: bool = True) -> None:
        self._write = write

    def is_locked(self) -> bool:
        return self._locked

    def locked(self, is_locked: bool = True) -> TestLocker:
        self._locked = is_locked

        return self

    def mock_lock_data(self, data: dict[str, Any]) -> None:
        self.locked()

        self._lock_data = data

    def is_fresh(self) -> bool:
        return True

    def _write_lock_data(self, data: TOMLDocument) -> None:
        if self._write:
            super()._write_lock_data(data)
            self._locked = True
            return

        self._lock_data = data


class TestRepository(Repository):
    def find_packages(self, dependency: Dependency) -> list[Package]:
        packages = super().find_packages(dependency)
        if len(packages) == 0:
            raise PackageNotFound(f"Package [{dependency.name}] not found.")

        return packages

    def find_links_for_package(self, package: Package) -> list[Link]:
        return [
            Link(
                f"https://foo.bar/files/{package.name.replace('-', '_')}"
                f"-{package.version.to_string()}-py2.py3-none-any.whl"
            )
        ]


def get_package(name: str, version: str | Version, yanked: str | bool = False) -> Package:
    return Package(name, version, yanked=yanked)
