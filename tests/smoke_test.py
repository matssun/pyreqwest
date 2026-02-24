"""Smoke test: verify pyreqwest native module loads and basic types are accessible."""

import pyreqwest
from pyreqwest.http import Url, HeaderMap


def test_version_available():
    assert hasattr(pyreqwest, "__version__")
    assert isinstance(pyreqwest.__version__, str)


def test_url_parsing():
    url = Url("https://example.com/path?key=value")
    assert str(url) == "https://example.com/path?key=value"


def test_header_map():
    headers = HeaderMap({"content-type": "application/json"})
    assert "content-type" in headers
