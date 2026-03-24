"""
hands/core/convert_csv_to_json.py

ConvertCsvToJsonHand implements the <convert-csv-to-json> tag.
Converts CSV content to a JSON array of objects.

Usage in XML:
    <box-def name="data_json">
        <convert-csv-to-json>
            <box name="csv"/>
        </convert-csv-to-json>
    </box-def>

    <!-- from file -->
    <box-def name="csv">
        <file-read path="feeds/corredora.csv"/>
    </box-def>
    <box-def name="data_json">
        <convert-csv-to-json>
            <box name="csv"/>
        </convert-csv-to-json>
    </box-def>

Input CSV format:
    nombre,precio
    Casa,100000
    Depto,80000

Output JSON format:
    [{"nombre": "Casa", "precio": "100000"}, {"nombre": "Depto", "precio": "80000"}]
"""

from __future__ import annotations
import json
import csv
import io
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FNodeVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand


@hand(tag="convert-csv-to-json")
class ConvertCsvToJsonHand(AbstractHand):
    """
    Converts CSV content to a JSON array of objects.
    The first row is used as the header (field names).

    Attributes:
        delimiter (optional): CSV delimiter character. Default: ,

    Returns:
        FNodeVariable with the JSON array string.
        FEmptyVariable if input is empty.

    Raises:
        ValueError if the input is not valid CSV.

    Examples:
        <box-def name="data_json">
            <convert-csv-to-json>
                <box name="csv"/>
            </convert-csv-to-json>
        </box-def>

        <!-- with custom delimiter -->
        <box-def name="data_json">
            <convert-csv-to-json delimiter=";">
                <box name="csv"/>
            </convert-csv-to-json>
        </box-def>
    """

    def execute(self) -> FVariable:
        from francis_suite.core.expressions import FrancisExpression
        engine    = FrancisExpression(self.context)
        delimiter = engine.resolve(self.attr("delimiter", ","))

        if self.has_children():
            result = self.execute_children()
            if result.is_empty():
                return FEmptyVariable()
            raw = result.to_string()
        else:
            raw = self.resolve_body_text()
            if not raw.strip():
                return FEmptyVariable()

        try:
            reader = csv.DictReader(
                io.StringIO(raw),
                delimiter=delimiter,
            )
            data = [dict(row) for row in reader]
        except Exception as e:
            raise ValueError(
                f"<convert-csv-to-json> invalid CSV input: {e}"
            ) from e

        if not data:
            return FEmptyVariable()

        return FNodeVariable(json.dumps(data, ensure_ascii=False))
