__all__ = ["version", "version_info"]


version = "3.0.0b7"
version_info = (3, 0, 0, "beta", 7)
# version_info has the same format as django.VERSION
# https://github.com/django/django/blob/4a5048b036fd9e965515e31fdd70b0af72655cba/django/utils/version.py#L22
#
# examples
# "3.0.0" -> (3, 0, 0, "final", 0)
# "3.0.0rc1" -> (3, 0, 0, "rc", 1)
# "3.0.0b7" -> (3, 0, 0, "beta", 7)
# "3.0.0a2" -> (3, 0, 0, "alpha", 2)
#
# also see tests/test_version.py
