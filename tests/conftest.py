"""
Pytest defaults — disable automatic private record metadata files during the suite
unless a test enables FRANCIS_AUTO_RECORD_METADATA explicitly.
"""

import pytest


@pytest.fixture(autouse=True)
def disable_auto_record_private_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FRANCIS_AUTO_RECORD_METADATA", "0")
