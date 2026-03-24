"""
core/records.py

Core data structures for the Francis Suite record system.
Records are structured collections of data with defined schemas.

Created by:   record-create
Populated by: record-add
Inspected by: record-last-added, record-count
Persisted by: record-save, record-save-meta

The record lives in the global context as a shared-box.
All hands access it by name — just like any other shared-box.

FVariable is imported from core/base.py to avoid circular imports
with core/variables.py — both modules need the same FVariable class.

Metadata system:
    Private metadata — always generated automatically, never fails
    Public metadata  — optional, only if <record-metadata> tag is present
"""

from __future__ import annotations
import json
import csv
import uuid
import re
import sys
import socket
import platform
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from francis_suite.core.base import FVariable


# ---------------------------------------------------------------------------
# Francis Suite version
# ---------------------------------------------------------------------------

FRANCIS_SUITE_VERSION = "0.1.0"


# ---------------------------------------------------------------------------
# Available auto fields for <metadata-field name="..."/>
# These are computed from the record itself at save time
# ---------------------------------------------------------------------------

AUTO_METADATA_FIELDS = {
    # data quality
    "total_rows",
    "rows_completados",
    "rows_con_campos_vacios",
    "rows_fallidos",
    "campos_nulos_total",
    "porcentaje_completitud",
    # performance
    "duracion_segundos",
    "rows_por_segundo",
    # traceability
    "session_id",
    "workflow_path",
    "francis_suite_version",
    "hostname",
    "sistema_operativo",
    "python_version",
    "status",
    "error",
    "inicio",
    "fin",
}


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
    """Defines a single field in a record schema."""

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

        # public metadata — optional, set by <record-metadata>
        # list of {"name": str, "value": str | None}
        # value=None means auto-computed at save time
        self.public_metadata_fields: list[dict] = []
        self.has_public_metadata: bool = False

    def add_group(self, group: FRecordGroup) -> None:
        self.groups[group.name] = group

    def add_public_metadata_field(self, name: str, value: str | None = None) -> None:
        """Add a field to public metadata. value=None means auto-computed."""
        self.has_public_metadata = True
        self.public_metadata_fields.append({"name": name, "value": value})

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
# FRecord
# ---------------------------------------------------------------------------

class FRecord(FVariable):
    """
    A structured collection of records with a defined schema.
    Inherits FVariable from core/base.py.

    Metadata system:
        Private metadata — always generated automatically, never fails
        Public metadata  — optional, only if schema.has_public_metadata is True
    """

    def __init__(self, schema: FRecordSchema) -> None:
        self._schema        = schema
        self._rows:         list[dict] = []
        self._rows_failed:  int = 0
        self._private_meta: dict = {}

        # RAM tracking with psutil if available
        self._ram_samples:  list[float] = []
        self._ram_peak:     float | None = None
        self._sample_ram()

    def _sample_ram(self) -> None:
        """Sample current RAM usage. Silently skips if psutil not available."""
        try:
            import psutil
            import os
            process   = psutil.Process(os.getpid())
            ram_mb    = process.memory_info().rss / 1024 / 1024
            self._ram_samples.append(ram_mb)
            if self._ram_peak is None or ram_mb > self._ram_peak:
                self._ram_peak = ram_mb
        except Exception:
            pass

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
        self._sample_ram()
        return normalized

    def add_private_metadata(self, name: str, value: str) -> None:
        """Add a custom field to private metadata."""
        self._private_meta[name] = value

    # --- Data quality stats ---

    def _compute_quality(self) -> dict:
        """Compute data quality stats from rows."""
        if not self._rows:
            return {
                "total_rows":              0,
                "rows_completados":        0,
                "rows_con_campos_vacios":  0,
                "rows_fallidos":           self._rows_failed,
                "campos_nulos_total":      0,
                "porcentaje_completitud":  None,
            }

        rows_con_vacios = 0
        campos_nulos    = 0

        for row in self._rows:
            flat = self._flatten(row)
            tiene_vacio = False
            for v in flat.values():
                if v is None or v == "":
                    campos_nulos += 1
                    tiene_vacio   = True
            if tiene_vacio:
                rows_con_vacios += 1

        total             = len(self._rows)
        rows_completados  = total - rows_con_vacios
        completitud       = round((rows_completados / total) * 100, 2) if total > 0 else None

        return {
            "total_rows":              total,
            "rows_completados":        rows_completados,
            "rows_con_campos_vacios":  rows_con_vacios,
            "rows_fallidos":           self._rows_failed,
            "campos_nulos_total":      campos_nulos,
            "porcentaje_completitud":  completitud,
        }

    # --- Private metadata generation ---

    def build_private_metadata(self, session=None) -> dict:
        """
        Build complete private metadata.
        Always returns all fields — missing values are None.
        Never raises — designed to work even if session is None or failed.
        """
        self._sample_ram()

        quality = self._compute_quality()

        # performance
        duracion        = None
        rows_por_segundo = None
        inicio          = None
        fin             = None
        session_id      = None
        workflow_path   = None
        status          = None
        error           = None

        if session is not None:
            try:
                session_id    = session.id
                workflow_path = session.workflow_name
                status        = session.status.value
                error         = str(session.error) if session.error else None
                inicio        = session.started_at.isoformat() if session.started_at else None
                fin           = session.finished_at.isoformat() if session.finished_at else None
                duracion      = session.duration
                if duracion and quality["total_rows"]:
                    rows_por_segundo = round(quality["total_rows"] / duracion, 2)
            except Exception:
                pass

        # RAM
        ram_peak    = self._ram_peak
        ram_promedio = round(sum(self._ram_samples) / len(self._ram_samples), 2) if self._ram_samples else None

        # system info
        try:
            hostname = socket.gethostname()
        except Exception:
            hostname = None

        try:
            so = platform.system() + "-" + platform.release()
        except Exception:
            so = None

        try:
            py_version = sys.version.split()[0]
        except Exception:
            py_version = None

        meta = {
            # traceability
            "session_id":              session_id,
            "workflow_path":           workflow_path,
            "francis_suite_version":   FRANCIS_SUITE_VERSION,
            "hostname":                hostname,
            "sistema_operativo":       so,
            "python_version":          py_version,
            "status":                  status,
            "error":                   error,
            "inicio":                  inicio,
            "fin":                     fin,

            # performance
            "duracion_segundos":               duracion,
            "ram_peak_mb":                     ram_peak,
            "ram_promedio_mb":                 ram_promedio,
            "rows_por_segundo":                rows_por_segundo,
            "requests_http_total":             None,  # future: httpx tracker
            "requests_http_fallidas":          None,  # future: httpx tracker
            "tiempo_promedio_por_request_ms":  None,  # future: httpx tracker

            # data quality
            "total_rows":              quality["total_rows"],
            "rows_completados":        quality["rows_completados"],
            "rows_con_campos_vacios":  quality["rows_con_campos_vacios"],
            "rows_fallidos":           quality["rows_fallidos"],
            "campos_nulos_total":      quality["campos_nulos_total"],
            "porcentaje_completitud":  quality["porcentaje_completitud"],

            # scraping specific — populated by <record-private-metadata>
            "paginas_procesadas":      self._private_meta.get("paginas_procesadas", None),
            "paginas_fallidas":        self._private_meta.get("paginas_fallidas", None),
            "urls_visitadas":          self._private_meta.get("urls_visitadas", None),
            "proxies_usados":          None,  # future: proxy system
            "captchas_encontrados":    None,  # future: playwright
            "rate_limits_alcanzados":  None,  # future: httpx tracker
        }

        # add any extra private fields the user added
        for key, value in self._private_meta.items():
            if key not in meta:
                meta[key] = value

        return meta

    # --- Public metadata generation ---

    def build_public_metadata(self, session=None) -> dict | None:
        """
        Build public metadata from declared fields.
        Returns None if no public metadata was declared.
        Only called when status=completed.
        """
        if not self._schema.has_public_metadata:
            return None

        private = self.build_private_metadata(session)
        quality = self._compute_quality()
        all_auto = {**private, **quality}

        result = {}
        for field in self._schema.public_metadata_fields:
            name  = field["name"]
            value = field["value"]

            if value is not None:
                # user provided a fixed value
                result[name] = value
            elif name in all_auto:
                # auto-computed field
                result[name] = all_auto[name]
            else:
                result[name] = None

        return result

    # --- FVariable interface ---

    def to_string(self) -> str:
        return f"[RECORD:{self.name}:{self.count}]"

    def to_display(self) -> str:
        return self.to_string()

    def to_list(self) -> list:
        return list(self._rows)

    def is_empty(self) -> bool:
        return len(self._rows) == 0

    # --- Persistence ---

    def save(self, format: str, path: str, include_metadata: bool = False, session=None) -> None:
        """
        Persist the record collection to disk.

        Args:
            format:           json, csv, ndjson
            path:             output file path
            include_metadata: if True, wraps output with public metadata (json only)
            session:          FrancisSession — used to compute metadata fields
        """
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        fmt = format.lower().strip()

        if fmt == "json":
            self._save_json(output_path, include_metadata=include_metadata, session=session)
        elif fmt == "csv":
            self._save_csv(output_path, include_metadata=include_metadata)
        elif fmt == "ndjson":
            self._save_ndjson(output_path, include_metadata=include_metadata, session=session)
        else:
            raise ValueError(
                f"[RECORD] unsupported format '{format}'. "
                f"Valid formats: json, csv, ndjson"
            )

        print(f"[RECORD] saved {self.count} rows to '{output_path}' as {fmt}")

    def save_meta(self, path: str, session=None) -> None:
        """
        Persist only the private metadata to disk as JSON.
        Always works — even if the session failed.
        """
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        meta = self.build_private_metadata(session)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2, default=str)

        print(f"[RECORD] saved metadata to '{output_path}'")

    def _save_json(self, path: Path, include_metadata: bool = False, session=None) -> None:
        if include_metadata:
            public_meta = self.build_public_metadata(session)
            output = {
                "_metadata": public_meta or {},
                "data": self._rows,
            }
        else:
            output = self._rows

        with open(path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2, default=str)

    def _save_ndjson(self, path: Path, include_metadata: bool = False, session=None) -> None:
        with open(path, "w", encoding="utf-8") as f:
            if include_metadata:
                public_meta = self.build_public_metadata(session)
                if public_meta:
                    f.write(json.dumps({"_type": "metadata", **public_meta}, ensure_ascii=False, default=str) + "\n")
            for row in self._rows:
                f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")

    def _save_csv(self, path: Path, include_metadata: bool = False) -> None:
        if not self._rows:
            return

        flat_rows = [self._flatten(row) for row in self._rows]

        keys: list[str] = []
        for row in flat_rows:
            for key in row:
                if key not in keys:
                    keys.append(key)

        with open(path, "w", encoding="utf-8", newline="") as f:
            if include_metadata and self._schema.has_public_metadata:
                # write metadata as comments at the top
                for field in self._schema.public_metadata_fields:
                    value = field["value"] or ""
                    f.write(f"# {field['name']}: {value}\n")

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
