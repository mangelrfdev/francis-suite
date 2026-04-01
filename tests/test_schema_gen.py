"""Tests for workflow XSD / JSON manifest generation."""

from __future__ import annotations

import json
from pathlib import Path

from francis_suite.schema_gen import (
    build_json_manifest,
    build_xsd,
    registered_tags_sorted,
    write_schemas,
)


def test_registered_tags_non_empty():
    tags = registered_tags_sorted()
    assert len(tags) >= 10
    assert "log" in tags
    assert tags == sorted(tags)


def test_xsd_contains_root_and_sample_tags():
    tags = registered_tags_sorted()
    xsd = build_xsd(tags)
    assert 'name="francis-workflow"' in xsd
    assert 'name="log"' in xsd
    assert "HandMixedType" in xsd


def test_json_manifest_roundtrip():
    tags = ["a", "b"]
    m = build_json_manifest(tags, version="9.9.9")
    assert m["hand_tags"] == tags
    assert m["francis_suite_version"] == "9.9.9"
    assert m["root_element"] == "francis-workflow"


def test_write_schemas(tmp_path: Path):
    xsd_path, json_path = write_schemas(tmp_path, version="0.0.0-test")
    assert xsd_path.exists()
    assert json_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["francis_suite_version"] == "0.0.0-test"
    assert isinstance(data["hand_tags"], list)
