from typing import Any, Tuple

import packaging
import pytest
from packaging.version import Version

from graphql_server.version import (
    version as VERSION,
    version_info as VERSION_INFO,
)

VersionInfoType = Tuple[int, int, int, str, int]

RELEASE_LEVEL = {"alpha": "a", "beta": "b", "rc": "rc", "final": None}

VERSION_AND_VERSION_INFO = [
    (
        "1.2.3",
        (1, 2, 3, "final", 0),
    ),
    (
        "1.2.3a4",
        (1, 2, 3, "alpha", 4),
    ),
    (
        "1.2.3b4",
        (1, 2, 3, "beta", 4),
    ),
    (
        "12.34.56rc789",
        (12, 34, 56, "rc", 789),
    ),
    (
        VERSION,
        VERSION_INFO,
    ),
]


@pytest.fixture(params=VERSION_AND_VERSION_INFO)
def version_and_version_info(
    request: pytest.FixtureRequest,
) -> Tuple[str, VersionInfoType]:
    return request.param


@pytest.fixture
def version(version_and_version_info: Tuple[str, VersionInfoType]) -> str:
    return version_and_version_info[0]


@pytest.fixture
def version_info(
    version_and_version_info: Tuple[str, VersionInfoType]
) -> VersionInfoType:
    return version_and_version_info[1]


@pytest.fixture
def parsed_version(version: str) -> Version:
    return Version(version)


def test_valid_version(version: str) -> None:
    packaging.version.parse(version)


def test_valid_version_info(version_info: Any) -> None:
    """version_info has to be a tuple[int, int, int, str, int]"""
    assert isinstance(version_info, tuple)
    assert len(version_info) == 5

    major, minor, micro, release_level, serial = version_info
    assert isinstance(major, int)
    assert isinstance(minor, int)
    assert isinstance(micro, int)
    assert isinstance(release_level, str)
    assert isinstance(serial, int)


def test_valid_version_release_level(parsed_version: Version) -> None:
    if parsed_version.pre is not None:
        valid_release_levels = {v for v in RELEASE_LEVEL.values() if v is not None}
        assert parsed_version.pre[0] in valid_release_levels


def test_valid_version_info_release_level(version_info: VersionInfoType) -> None:
    assert version_info[3] in RELEASE_LEVEL.keys()


def test_version_same_as_version_info(
    parsed_version: Version, version_info: VersionInfoType
) -> None:
    assert (
        parsed_version.major,
        parsed_version.minor,
        parsed_version.micro,
    ) == version_info[:3]

    release_level, serial = version_info[-2:]
    if parsed_version.is_prerelease:
        assert (RELEASE_LEVEL[release_level], serial) == parsed_version.pre
    else:
        assert (release_level, serial) == ("final", 0)
