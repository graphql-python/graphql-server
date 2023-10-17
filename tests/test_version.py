import packaging
from packaging.version import Version

from graphql_server.version import version, version_info

RELEASE_LEVEL = {"alpha": "a", "beta": "b", "rc": "rc", "final": None}


parsed_version = Version(version)


def test_valid_version() -> None:
    packaging.version.parse(version)


def test_valid_version_info() -> None:
    """version_info has to be a tuple[int, int, int, str, int]"""
    assert isinstance(version_info, tuple)
    assert len(version_info) == 5

    major, minor, micro, release_level, serial = version_info
    assert isinstance(major, int)
    assert isinstance(minor, int)
    assert isinstance(micro, int)
    assert isinstance(release_level, str)
    assert isinstance(serial, int)


def test_valid_version_release_level() -> None:
    if parsed_version.pre is not None:
        valid_release_levels = {v for v in RELEASE_LEVEL.values() if v is not None}
        assert parsed_version.pre[0] in valid_release_levels


def test_valid_version_info_release_level() -> None:
    assert version_info[3] in RELEASE_LEVEL.keys()


def test_version_same_as_version_info() -> None:
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
