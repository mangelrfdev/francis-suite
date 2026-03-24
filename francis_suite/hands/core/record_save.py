"""
hands/core/record_save.py

RecordSaveHand implements the <record-save> tag.
Persists a record collection to disk in the specified format.

Usage in XML:
    <!-- data only — default, no metadata -->
    <record-save from="propiedadesRecords" format="ndjson" path="output/propiedades.ndjson"/>

    <!-- data with public metadata — only if <record-metadata> was declared -->
    <record-save from="propiedadesRecords" format="json"
                 path="output/propiedades.json"
                 include-metadata="true"/>
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FEmptyVariable
from francis_suite.core.records import FRecord
from francis_suite.core.expressions import FrancisExpression
from francis_suite.hands.base import AbstractHand


@hand(tag="record-save")
class RecordSaveHand(AbstractHand):
    """
    Persists a record collection to disk.

    Attributes:
        from             (required): name of the record collection.
        format           (required): output format — json, csv, ndjson.
        path             (required): output file path. Supports ${variables}.
        include-metadata (optional): include public metadata in output. Default: false.

    Formats:
        json   — array of nested objects — for APIs and web systems
        csv    — flat rows with dot notation — for Excel, Sheets, Pandas
        ndjson — one JSON per line — ideal for BigQuery, Spark, Polars

    Notes:
        - include-metadata only works if <record-metadata> was declared in record-create
        - Public metadata is only written when status=completed
        - For private/full metadata use <record-save-meta>

    Returns:
        FEmptyVariable always.

    Examples:
        <!-- data only -->
        <record-save from="productosRecords" format="ndjson" path="output/productos.ndjson"/>

        <!-- data with public metadata -->
        <record-save from="productosRecords" format="json"
                     path="output/productos.json"
                     include-metadata="true"/>
    """

    def execute(self) -> FVariable:
        engine           = FrancisExpression(self.context)
        record_name      = engine.resolve(self.require_attr("from"))
        fmt              = engine.resolve(self.require_attr("format"))
        path             = engine.resolve(self.require_attr("path"))
        include_metadata = self.attr("include-metadata", "false").lower() == "true"

        record = self.context.get_shared_box(record_name)

        if not isinstance(record, FRecord):
            raise ValueError(
                f"[RECORD] record '{record_name}' not found. "
                f"Make sure <record-create name=\"{record_name}\"> runs first."
            )

        if record.is_empty():
            print(f"[RECORD] '{record_name}' is empty — skipping save to '{path}'")
            return FEmptyVariable()

        record.save(
            format           = fmt,
            path             = path,
            include_metadata = include_metadata,
            session          = self.session,
        )
        return FEmptyVariable()
