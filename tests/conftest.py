from __future__ import annotations

import shutil
import sys

from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any
from typing import Iterator
from typing import Mapping

import pytest

from cleo.io.null_io import NullIO
from cleo.testers.command_tester import CommandTester
from poetry.config.config import Config as BaseConfig
from poetry.config.dict_config_source import DictConfigSource
from poetry.console.commands.env_command import EnvCommand
from poetry.factory import Factory
from poetry.layouts import layout
from poetry.repositories import Repository
from poetry.repositories.repository_pool import RepositoryPool
from poetry.utils.env import EnvManager
from poetry.utils.env import MockEnv
from poetry.utils.env import SystemEnv
from poetry.utils.env import VirtualEnv

from tests.helpers import CommandTesterFactory
from tests.helpers import FixtureCopier
from tests.helpers import FixtureDirGetter
from tests.helpers import PoetryTestApplication
from tests.helpers import ProjectFactory
from tests.helpers import TestLocker
from tests.helpers import TestRepository
from tests.helpers import get_package


if TYPE_CHECKING:
    from poetry.installation import Installer
    from poetry.installation.executor import Executor
    from poetry.poetry import Poetry
    from poetry.utils.env import Env
    from pytest_mock import MockerFixture


class Config(BaseConfig):
    def get(self, setting_name: str, default: Any = None) -> Any:
        self.merge(self._config_source.config)  # type: ignore[attr-defined]
        self.merge(self._auth_config_source.config)  # type: ignore[attr-defined]

        return super().get(setting_name, default=default)

    def raw(self) -> dict[str, Any]:
        self.merge(self._config_source.config)  # type: ignore[attr-defined]
        self.merge(self._auth_config_source.config)  # type: ignore[attr-defined]

        return super().raw()

    def all(self) -> dict[str, Any]:
        self.merge(self._config_source.config)  # type: ignore[attr-defined]
        self.merge(self._auth_config_source.config)  # type: ignore[attr-defined]

        return super().all()


@pytest.fixture
def config_cache_dir(tmp_path: Path) -> Path:
    path = tmp_path / ".cache" / "pypoetry"
    path.mkdir(parents=True)

    return path


@pytest.fixture
def config_source(config_cache_dir: Path) -> DictConfigSource:
    source = DictConfigSource()
    source.add_property("cache-dir", str(config_cache_dir))

    return source


@pytest.fixture
def auth_config_source() -> DictConfigSource:
    source = DictConfigSource()

    return source


@pytest.fixture
def config(
    config_source: DictConfigSource,
    auth_config_source: DictConfigSource,
    mocker: MockerFixture,
) -> Config:
    import keyring

    from keyring.backends.fail import Keyring

    keyring.set_keyring(Keyring())  # type: ignore[no-untyped-call]

    c = Config()
    c.merge(config_source.config)
    c.set_config_source(config_source)
    c.set_auth_config_source(auth_config_source)

    mocker.patch("poetry.config.config.Config.create", return_value=c)
    mocker.patch("poetry.config.config.Config.set_config_source")

    return c


@pytest.fixture(scope="session")
def fixture_base() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def fixture_dir(fixture_base: Path) -> FixtureDirGetter:
    def _fixture_dir(name: str) -> Path:
        return fixture_base / name

    return _fixture_dir


@pytest.fixture()
def repo() -> Repository:
    return Repository("repo")


@pytest.fixture
def installed() -> Repository:
    return Repository("installed")


@pytest.fixture(scope="session")
def current_env() -> SystemEnv:
    return SystemEnv(Path(sys.executable))


@pytest.fixture(scope="session")
def current_python(current_env: SystemEnv) -> tuple[Any, ...]:
    return current_env.version_info[:3]


@pytest.fixture(scope="session")
def default_python(current_python: tuple[int, int, int]) -> str:
    return "^" + ".".join(str(v) for v in current_python[:2])


@pytest.fixture
def project_directory() -> str:
    return "simple_project"


@pytest.fixture
def required_fixtures() -> list[str]:
    return []


@pytest.fixture
def fixture_copier(fixture_base: Path, tmp_path: Path) -> FixtureCopier:
    def _copy(relative_path: str, target: Path | None = None) -> Path:
        path = fixture_base / relative_path
        target = target or (tmp_path / relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        if target.exists():
            return target

        if path.is_dir():
            shutil.copytree(path, target)
        else:
            shutil.copyfile(path, target)

        return target

    return _copy


@pytest.fixture(autouse=True)
def load_required_fixtures(required_fixtures: list[str], fixture_copier: FixtureCopier) -> None:
    for fixture in required_fixtures:
        fixture_copier(fixture)


@pytest.fixture
def project_factory(
    tmp_path: Path,
    config: Config,
    repo: TestRepository,
    installed: Repository,
    default_python: str,
    load_required_fixtures: None,
) -> ProjectFactory:
    workspace = tmp_path

    def _factory(
        name: str | None = None,
        dependencies: Mapping[str, str] | None = None,
        dev_dependencies: Mapping[str, str] | None = None,
        pyproject_content: str | None = None,
        poetry_lock_content: str | None = None,
        install_deps: bool = True,
        source: Path | None = None,
        locker_config: dict[str, Any] | None = None,
        use_test_locker: bool = True,
    ) -> Poetry:
        project_dir = workspace / f"poetry-fixture-{name}"
        dependencies = dependencies or {}
        dev_dependencies = dev_dependencies or {}

        if pyproject_content or source:
            if source:
                project_dir.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(source, project_dir)
            else:
                project_dir.mkdir(parents=True, exist_ok=True)

            if pyproject_content:
                with (project_dir / "pyproject.toml").open("w", encoding="utf-8") as f:
                    f.write(pyproject_content)
        else:
            assert name is not None
            layout("src")(
                name,
                "0.1.0",
                author="PyTest Tester <mc.testy@testface.com>",
                readme_format="md",
                python=default_python,
                dependencies=dependencies,
                dev_dependencies=dev_dependencies,
            ).create(project_dir, with_tests=False)

        if poetry_lock_content:
            lock_file = project_dir / "poetry.lock"
            lock_file.write_text(data=poetry_lock_content, encoding="utf-8")

        poetry = Factory().create_poetry(project_dir)

        if use_test_locker:
            locker = TestLocker(poetry.locker.lock, locker_config or poetry.locker._local_config)
            locker.write()

            poetry.set_locker(locker)

        poetry.set_config(config)

        pool = RepositoryPool()
        pool.add_repository(repo)

        poetry.set_pool(pool)

        if install_deps:
            for deps in [dependencies, dev_dependencies]:
                for name, version in deps.items():
                    pkg = get_package(name, version)
                    repo.add_package(pkg)
                    installed.add_package(pkg)

        return poetry

    return _factory


@pytest.fixture
def app(poetry: Poetry) -> PoetryTestApplication:
    app_ = PoetryTestApplication(poetry)

    return app_


@pytest.fixture
def env(tmp_path: Path) -> MockEnv:
    path = tmp_path / ".venv"
    path.mkdir(parents=True)
    return MockEnv(path=path, is_venv=True)


@pytest.fixture
def tmp_venv(tmp_path: Path) -> Iterator[VirtualEnv]:
    venv_path = tmp_path / "venv"

    EnvManager.build_venv(venv_path)

    venv = VirtualEnv(venv_path)
    yield venv

    shutil.rmtree(venv.path)


@pytest.fixture
def command_tester_factory(app: PoetryTestApplication, env: MockEnv) -> CommandTesterFactory:
    def _tester(
        command: str,
        poetry: Poetry | None = None,
        installer: Installer | None = None,
        executor: Executor | None = None,
        environment: Env | None = None,
    ) -> CommandTester:
        app._load_plugins(NullIO())

        cmd = app.find(command)
        tester = CommandTester(cmd)

        # Setting the formatter from the application
        # TODO: Find a better way to do this in Cleo
        app_io = app.create_io()
        formatter = app_io.output.formatter
        tester.io.output.set_formatter(formatter)
        tester.io.error_output.set_formatter(formatter)

        if poetry:
            app._poetry = poetry

        poetry = app.poetry

        if isinstance(cmd, EnvCommand):
            cmd.set_env(environment or env)

        return tester

    return _tester
