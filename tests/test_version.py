import re
from typing import Tuple, Union

import pytest

import graphql_server
from graphql_server.version import VersionInfo, version, version_info

_re_version = re.compile(r"(\d+)\.(\d+)\.(\d+)(?:([abc]|rc)(\d+))?$")

TEST_CASES = [
    (
        (1, 2, 3),
        "1.2.3",
    ),
    (
        (1, 2, 3, "alpha", 4),
        "1.2.3a4",
    ),
    (
        (1, 2, 3, "beta", 4),
        "1.2.3b4",
    ),
    (
        (12, 34, 56, "candidate", 789),
        "12.34.56rc789",
    ),
]


PARSED_VERSIONS = [parsed_version for parsed_version, _ in TEST_CASES]
VERSION_STRINGS = [version_string for _, version_string in TEST_CASES]


def extract_version_components(
    parsed_version: Union[Tuple[int, int, int], Tuple[int, int, int, str, int]],
) -> Tuple[int, int, int, str, int]:
    if len(parsed_version) == 5:
        return parsed_version  # type: ignore
    elif len(parsed_version) == 3:
        return tuple([*parsed_version, "final", 0])  # type: ignore

    raise ValueError("parsed_version length should be either 3 or 5")


@pytest.mark.parametrize("parsed_version", PARSED_VERSIONS)
def test_create_version_info_from_fields(
    parsed_version: Union[Tuple[int, int, int], Tuple[int, int, int, str, int]],
) -> None:
    version_components = extract_version_components(parsed_version)
    major, minor, micro, releaselevel, serial = version_components
    v = VersionInfo(*version_components)

    assert v.major == major
    assert v.minor == minor
    assert v.micro == micro
    assert v.releaselevel == releaselevel
    assert v.serial == serial


@pytest.mark.parametrize("parsed_version, version_string", TEST_CASES)
def test_create_version_info_from_str(
    parsed_version: Union[Tuple[int, int, int], Tuple[int, int, int, str, int]],
    version_string: str,
) -> None:
    v = VersionInfo.from_str(version_string)
    major, minor, micro, releaselevel, serial = extract_version_components(
        parsed_version
    )

    assert v.major == major
    assert v.minor == minor
    assert v.micro == micro
    assert v.releaselevel == releaselevel
    assert v.serial == serial


@pytest.mark.parametrize("parsed_version, version_string", TEST_CASES)
def test_serialize_as_str(
    parsed_version: Union[Tuple[int, int, int], Tuple[int, int, int, str, int]],
    version_string: str,
) -> None:
    v = VersionInfo(*extract_version_components(parsed_version))
    assert str(v) == version_string


def test_base_package_has_correct_version() -> None:
    assert graphql_server.__version__ == version
    assert graphql_server.version == version


def test_base_package_has_correct_version_info() -> None:
    assert graphql_server.__version_info__ is version_info
    assert graphql_server.version_info is version_info


@pytest.mark.parametrize("version", VERSION_STRINGS + [version])
def test_version_has_correct_format(version: str) -> None:
    assert isinstance(version, str)
    assert _re_version.match(version)


@pytest.mark.parametrize(
    "version,version_info",
    zip(
        VERSION_STRINGS + [version],
        [VersionInfo.from_str(v) for v in VERSION_STRINGS] + [version_info],
    ),
)
def test_version_info_has_correct_fields(
    version: str, version_info: VersionInfo
) -> None:
    assert isinstance(version_info, tuple)
    assert str(version_info) == version
    groups = _re_version.match(version).groups()  # type: ignore
    assert version_info.major == int(groups[0])
    assert version_info.minor == int(groups[1])
    assert version_info.micro == int(groups[2])
    if groups[3] is None:  # pragma: no cover
        assert groups[4] is None
    else:  # pragma: no cover
        if version_info.releaselevel == "candidate":
            assert groups[3] == "rc"
        else:
            assert version_info.releaselevel[:1] == groups[3]
        assert version_info.serial == int(groups[4])
