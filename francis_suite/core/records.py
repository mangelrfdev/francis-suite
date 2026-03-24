"""
core/records.py

Core data structures for the Francis Suite record system.
Records are structured collections of data with defined schemas.

Created by:   record-create
Populated by: record-add
Inspected by: record-last-added, record-count
Persisted by: record-save

The record lives in the global context as a shared-box.
All hands access it by name — just like any other shared-box.

FVariable is imported from core/base.py to avoid circular imports
with core/variables.py — both modules need the same FVariable class.
"""

from __future__ import annotations
import json
import csv
import uuid
import re
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from datetime import datetime
from pathlib import Path
from typing import Any
from francis_suite.core.base import FVariable


# ---------------------------------------------------------------------------
# Valid field types
# ---------------------------------------------------------------------------

VALID_TYPES = {
    "string",
    "integer",
    "decimal",
    "boolean",
    "date",
    "datetime",
    "url",
    "email",
    "uuid",
}

_TRUE_VALUES  = {"true", "yes", "si", "sí", "1", "verdadero"}
_FALSE_VALUES = {"false", "no", "0", "falso"}


# ---------------------------------------------------------------------------
# FRecordField
# ---------------------------------------------------------------------------

class FRecordField:
    """
    Defines a single field in a record schema.

    Attributes:
        name          — field name
        type          — data type (string, integer, decimal, etc.)
        required      — whether the field must have a value
        null_if_empty — if True, empty values are stored as None instead of ""
        precision     — decimal places for decimal type (None = full precision)
    """

    def __init__(
        self,
        name: str,
        field_type: str,
        required: bool = True,
        null_if_empty: bool = False,
        precision: str | None = None,
    ) -> None:
        if field_type not in VALID_TYPES:
            raise ValueError(
                f"[RECORD] invalid field type '{field_type}' for field '{name}'. "
                f"Valid types: {', '.join(sorted(VALID_TYPES))}"
            )

        self.name          = name
        self.type          = field_type
        self.required      = required
        self.null_if_empty = null_if_empty
        self.precision     = precision

    def normalize(self, raw_value: Any) -> Any:
        """Normalize and validate a raw value according to this field's type."""
        value = str(raw_value).strip() if raw_value is not None else ""

        if not value:
            if self.type == "uuid":
                return str(uuid.uuid4())
            if self.required:
                raise ValueError(
                    f"[RECORD] field '{self.name}' is required but got empty value"
                )
            return None if self.null_if_empty else ""

        if self.type == "string":
            return value
        elif self.type == "integer":
            return self._normalize_integer(value)
        elif self.type == "decimal":
            return self._normalize_decimal(value)
        elif self.type == "boolean":
            return self._normalize_boolean(value)
        elif self.type == "date":
            return self._normalize_date(value)
        elif self.type == "datetime":
            return self._normalize_datetime(value)
        elif self.type == "url":
            return self._normalize_url(value)
        elif self.type == "email":
            return self._normalize_email(value)
        elif self.type == "uuid":
            return self._normalize_uuid(value)

        return value

    def _normalize_integer(self, value: str) -> int:
        cleaned = re.sub(r"[^\d\-]", "", value.replace(",", ""))
        if not cleaned or cleaned == "-":
            raise ValueError(
                f"[RECORD] field '{self.name}' expects integer but got '{value}'"
            )
        try:
            return int(cleaned)
        except ValueError:
            raise ValueError(
                f"[RECORD] field '{self.name}' expects integer but got '{value}'"
            )

    def _normalize_decimal(self, value: str) -> str:
        if re.search(r"\d\.\d{3},", value):
            cleaned = re.sub(r"[^\d,\-]", "", value)
            cleaned = cleaned.replace(".", "").replace(",", ".")
        elif re.search(r"\d,\d{1,2}$", value):
            cleaned = re.sub(r"[^\d,\-]", "", value)
            cleaned = cleaned.replace(",", ".")
        else:
            cleaned = re.sub(r"[^\d\.\-]", "", value)

        if not cleaned or cleaned == "-":
            raise ValueError(
                f"[RECORD] field '{self.name}' expects decimal but got '{value}'"
            )

        try:
            decimal_value = Decimal(cleaned)
        except InvalidOperation:
            raise ValueError(
                f"[RECORD] field '{self.name}' expects decimal but got '{value}'"
            )

        if self.precision and self.precision != "raw":
            try:
                places = int(self.precision)
                quantize_str = "0." + "0" * places if places > 0 else "0"
                decimal_value = decimal_value.quantize(
                    Decimal(quantize_str),
                    rounding=ROUND_HALF_UP
                )
            except (ValueError, InvalidOperation):
                raise ValueError(
                    f"[RECORD] invalid precision '{self.precision}' for field '{self.name}'"
                )

        return str(decimal_value)

    def _normalize_boolean(self, value: str) -> bool:
        lower = value.lower().strip()
        if lower in _TRUE_VALUES:
            return True
        if lower in _FALSE_VALUES:
            return False
        raise ValueError(
            f"[RECORD] field '{self.name}' expects boolean but got '{value}'. "
            f"Valid values: {', '.join(sorted(_TRUE_VALUES | _FALSE_VALUES))}"
        )

    def _normalize_date(self, value: str) -> str:
        formats = [
            "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y",
            "%m/%d/%Y", "%d.%m.%Y", "%Y/%m/%d",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        raise ValueError(
            f"[RECORD] field '{self.name}' expects date but got '{value}'. "
            f"Supported formats: DD/MM/YYYY, YYYY-MM-DD, DD-MM-YYYY"
        )

    def _normalize_datetime(self, value: str) -> str:
        formats = [
            "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S",
            "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M",
            "%d-%m-%Y %H:%M:%S", "%d-%m-%Y %H:%M",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt).strftime("%Y-%m-%dT%H:%M:%S")
            except ValueError:
                continue
        raise ValueError(
            f"[RECORD] field '{self.name}' expects datetime but got '{value}'. "
            f"Supported formats: YYYY-MM-DDTHH:MM:SS, DD/MM/YYYY HH:MM:SS"
        )

    def _normalize_url(self, value: str) -> str:
        if not re.match(r"^https?://", value):
            raise ValueError(
                f"[RECORD] field '{self.name}' expects URL but got '{value}'. "
                f"URL must start with http:// or https://"
            )
        return value

    def _normalize_email(self, value: str) -> str:
        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", value):
            raise ValueError(
                f"[RECORD] field '{self.name}' expects email but got '{value}'"
            )
        return value.lower()

    def _normalize_uuid(self, value: str) -> str:
        try:
            return str(uuid.UUID(value))
        except ValueError:
            raise ValueError(
                f"[RECORD] field '{self.name}' expects UUID but got '{value}'"
            )


# ---------------------------------------------------------------------------
# FRecordGroup
# ---------------------------------------------------------------------------

class FRecordGroup:
    """A named group of fields within a record schema."""

    def __init__(self, name: str, required: bool = True) -> None:
        self.name     = name
        self.required = required
        self.fields: dict[str, FRecordField] = {}

    def add_field(self, field: FRecordField) -> None:
        self.fields[field.name] = field

    def normalize_row(self, raw_row: dict) -> dict:
        result = {}
        for field_name, field in self.fields.items():
            raw_value = raw_row.get(field_name, "")
            result[field_name] = field.normalize(raw_value)
        return result


# ---------------------------------------------------------------------------
# FRecordSchema
# ---------------------------------------------------------------------------

class FRecordSchema:
    """Complete schema for a record collection."""

    def __init__(self, name: str) -> None:
        self.name   = name
        self.groups: dict[str, FRecordGroup] = {}

    def add_group(self, group: FRecordGroup) -> None:
        self.groups[group.name] = group

    def normalize_row(self, raw_row: dict) -> dict:
        result = {}
        for group_name, group in self.groups.items():
            group_raw = {}
            for field_name in group.fields:
                key = f"{group_name}.{field_name}"
                group_raw[field_name] = raw_row.get(key, "")
            result[group_name] = group.normalize_row(group_raw)
        return result


# ---------------------------------------------------------------------------
# FRecord — inherits from the shared FVariable in core/base.py
# ---------------------------------------------------------------------------

class FRecord(FVariable):
    """
    A structured collection of records with a defined schema.
    Inherits FVariable from core/base.py — same class used by variables.py.
    This means isinstance(record, FVariable) works correctly everywhere.

    to_string() returns a readable tag — never actual data.
    This prevents accidental use in compose or log as if it were a string.

    Usage flow:
        record-create  → FRecord(schema) → context.set_shared_box(name, record)
        record-add     → record.add_row(raw_row)
        record-save    → record.save(format, path)
    """

    def __init__(self, schema: FRecordSchema) -> None:
        self._schema = schema
        self._rows:   list[dict] = []

    @property
    def name(self) -> str:
        return self._schema.name

    @property
    def count(self) -> int:
        return len(self._rows)

    @property
    def last_row(self) -> dict | None:
        return self._rows[-1] if self._rows else None

    def add_row(self, raw_row: dict) -> dict:
        """Normalize and add a row to the collection."""
        normalized = self._schema.normalize_row(raw_row)
        self._rows.append(normalized)
        return normalized

    # --- FVariable interface ---

    def to_string(self) -> str:
        """
        Returns a readable tag — NOT actual data.
        Prevents accidental use in compose or log.
        Example: [RECORD:propiedadesRecords:3]
        """
        return f"[RECORD:{self.name}:{self.count}]"

    def to_display(self) -> str:
        return self.to_string()

    def to_list(self) -> list:
        return list(self._rows)

    def is_empty(self) -> bool:
        return len(self._rows) == 0

    # --- Persistence ---

    def save(self, format: str, path: str) -> None:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        fmt = format.lower().strip()

        if fmt == "json":
            self._save_json(output_path)
        elif fmt == "csv":
            self._save_csv(output_path)
        elif fmt == "ndjson":
            self._save_ndjson(output_path)
        else:
            raise ValueError(
                f"[RECORD] unsupported format '{format}'. "
                f"Valid formats: json, csv, ndjson"
            )

        print(f"[RECORD] saved {self.count} rows to '{output_path}' as {fmt}")

    def _save_json(self, path: Path) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._rows, f, ensure_ascii=False, indent=2, default=str)

    def _save_ndjson(self, path: Path) -> None:
        with open(path, "w", encoding="utf-8") as f:
            for row in self._rows:
                f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")

    def _save_csv(self, path: Path) -> None:
        if not self._rows:
            return

        flat_rows = [self._flatten(row) for row in self._rows]

        keys: list[str] = []
        for row in flat_rows:
            for key in row:
                if key not in keys:
                    keys.append(key)

        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(flat_rows)

    def _flatten(self, obj: dict, prefix: str = "") -> dict:
        result = {}
        for key, value in obj.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                result.update(self._flatten(value, full_key))
            else:
                result[full_key] = value if value is not None else ""
        return result
