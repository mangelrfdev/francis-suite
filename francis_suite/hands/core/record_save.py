"""
hands/core/record_save.py

RecordSaveHand implements the <record-save> tag.
Persists a record collection to disk in the specified format.

Usage in XML:
    <record-save from="propiedadesRecords" format="json"   path="output/propiedades.json"/>
    <record-save from="propiedadesRecords" format="csv"    path="output/propiedades.csv"/>
    <record-save from="propiedadesRecords" format="ndjson" path="output/propiedades.ndjson"/>
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
        from   (required): name of the record collection.
        format (required): output format — json, csv, ndjson.
        path   (required): output file path. Supports ${variables}.

    Formats:
        json   — array of nested objects — for APIs and web systems
        csv    — flat rows with dot notation — for Excel, Sheets, Pandas
        ndjson — one JSON per line — ideal for BigQuery, Spark, Polars

    Returns:
        FEmptyVariable always.

    Examples:
        <record-save from="productosRecords" format="json"   path="output/productos.json"/>
        <record-save from="productosRecords" format="csv"    path="output/productos.csv"/>
        <record-save from="productosRecords" format="ndjson" path="output/productos.ndjson"/>

        <!-- dynamic path -->
        <record-save from="productosRecords" format="json" path="output/${fecha}/productos.json"/>
    """

    def execute(self) -> FVariable:
        engine      = FrancisExpression(self.context)
        record_name = engine.resolve(self.require_attr("from"))
        fmt         = engine.resolve(self.require_attr("format"))
        path        = engine.resolve(self.require_attr("path"))

        record = self.context.get_shared_box(record_name)

        if not isinstance(record, FRecord):
            raise ValueError(
                f"[RECORD] record '{record_name}' not found. "
                f"Make sure <record-create name=\"{record_name}\"> runs first."
            )

        if record.is_empty():
            print(f"[RECORD] '{record_name}' is empty — skipping save to '{path}'")
            return FEmptyVariable()

        record.save(format=fmt, path=path)
        return FEmptyVariable()
