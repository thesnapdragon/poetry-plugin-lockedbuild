from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from poetry.factory import Factory


if TYPE_CHECKING:
    from pathlib import Path

    from poetry.poetry import Poetry
    from poetry.utils.env import VirtualEnv

    from tests.helpers import CommandTesterFactory
    from tests.helpers import FixtureDirGetter
    from tests.helpers import ProjectFactory


@pytest.fixture
def poetry(
    project_directory: str,
    project_factory: ProjectFactory,
    fixture_dir: FixtureDirGetter,
) -> Poetry:
    return project_factory(name="simple")


@pytest.fixture
def required_fixtures() -> list[str]:
    return ["simple_project"]


def test_command_executed_successfully(
    tmp_path: Path,
    tmp_venv: VirtualEnv,
    command_tester_factory: CommandTesterFactory,
) -> None:
    target_dir = tmp_path / "simple_project"

    poetry = Factory().create_poetry(target_dir)
    tester = command_tester_factory("lockedbuild", poetry, environment=tmp_venv)

    tester.execute()

    build_dir = target_dir / "dist"
    assert build_dir.exists()

    (wheel_file,) = build_dir.glob("my_package-0.1-*.whl")
    assert wheel_file.exists()
    assert wheel_file.stat().st_size > 0
