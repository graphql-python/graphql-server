import pytest

from graphql_server.types import unset


def test_unset_singleton_and_representation():
    assert unset.UnsetType() is unset.UNSET
    assert str(unset.UNSET) == ""
    assert repr(unset.UNSET) == "UNSET"
    assert not unset.UNSET


def test_deprecated_is_unset_and_getattr():
    with pytest.warns(DeprecationWarning):
        assert unset.is_unset(unset.UNSET)
    with pytest.raises(AttributeError):
        unset.missing
