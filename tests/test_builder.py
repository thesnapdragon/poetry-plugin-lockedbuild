from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from pkginfo import Wheel
from poetry.factory import Factory

from poetry_plugin_lockedbuild.builder import LockedWheelBuilder


if TYPE_CHECKING:
    from pathlib import Path

    from poetry.utils.env import VirtualEnv


@pytest.fixture
def required_fixtures() -> list[str]:
    return ["simple_project", "simple_project_with_group", "simple_project_with_extras"]


def test_builder_sets_resolved_dependencies_in_metadata(tmp_path: Path, tmp_venv: VirtualEnv) -> None:
    target_dir = tmp_path / "simple_project"

    poetry = Factory().create_poetry(target_dir)
    LockedWheelBuilder(poetry, tmp_venv, poetry.locker).build()

    build_dir = target_dir / "dist"
    (wheel_file,) = build_dir.glob("my_package-0.1-*.whl")

    assert Wheel(str(wheel_file)).requires_dist == [
        "certifi (==2023.7.22)",
        "charset-normalizer (==3.3.0)",
        "idna (==3.4)",
        "requests (==2.31.0)",
        "urllib3 (==2.0.6)",
    ]


def test_builder_sets_resolved_dependencies_from_group_in_metadata(tmp_path: Path, tmp_venv: VirtualEnv) -> None:
    target_dir = tmp_path / "simple_project_with_group"

    poetry = Factory().create_poetry(target_dir)
    LockedWheelBuilder(poetry, tmp_venv, poetry.locker, with_groups=("my_group",)).build()

    build_dir = target_dir / "dist"
    (wheel_file,) = build_dir.glob("my_package-0.1-*.whl")

    assert Wheel(str(wheel_file)).requires_dist == [
        "certifi (==2023.7.22)",
        "charset-normalizer (==3.3.2)",
        "idna (==3.4)",
        "python-dateutil (==2.8.2)",
        "requests (==2.31.0)",
        "six (==1.16.0)",
        "urllib3 (==2.0.7)",
    ]


def test_builder_sets_resolved_dependencies_from_extras_in_metadata(tmp_path: Path, tmp_venv: VirtualEnv) -> None:
    target_dir = tmp_path / "simple_project_with_extras"

    poetry = Factory().create_poetry(target_dir)
    LockedWheelBuilder(poetry, tmp_venv, poetry.locker).build()

    build_dir = target_dir / "dist"
    (wheel_file,) = build_dir.glob("my_package-0.1-*.whl")

    assert Wheel(str(wheel_file)).requires_dist == [
        "certifi (==2023.7.22)",
        "charset-normalizer (==3.3.2)",
        "idna (==3.4)",
        "python-dateutil (==2.8.2)",
        'requests (==2.31.0) ; extra == "my-extra"',
        "six (==1.16.0)",
        "urllib3 (==2.0.7)",
    ]
