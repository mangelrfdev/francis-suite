"""
hands/core/convert_json_to_csv.py

ConvertJsonToCsvHand implements the <convert-json-to-csv> tag.
Converts a JSON array of objects to CSV format.

Usage in XML:
    <box-def name="csv">
        <convert-json-to-csv>
            <box name="data_json"/>
        </convert-json-to-csv>
    </box-def>

    <!-- save to disk -->
    <file-write path="output/datos.csv">
        <box name="csv"/>
    </file-write>

Input JSON format:
    [{"nombre": "Casa", "precio": 100000}, {"nombre": "Depto", "precio": 80000}]

Output CSV format:
    nombre,precio
    Casa,100000
    Depto,80000
"""

from __future__ import annotations
import json
import csv
import io
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FNodeVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand


@hand(tag="convert-json-to-csv")
class ConvertJsonToCsvHand(AbstractHand):
    """
    Converts a JSON array of objects to CSV format.

    Attributes:
        delimiter (optional): CSV delimiter character. Default: ,
        encoding (optional): output encoding. Default: utf-8

    Returns:
        FNodeVariable with the CSV string.
        FEmptyVariable if input is empty or not a valid JSON array.

    Raises:
        ValueError if the input is not valid JSON.
        ValueError if the input is not a JSON array of objects.

    Examples:
        <box-def name="csv">
            <convert-json-to-csv>
                <box name="data_json"/>
            </convert-json-to-csv>
        </box-def>

        <!-- with custom delimiter -->
        <box-def name="csv">
            <convert-json-to-csv delimiter=";">
                <box name="data_json"/>
            </convert-json-to-csv>
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
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"<convert-json-to-csv> invalid JSON input: {e}"
            ) from e

        if not isinstance(data, list):
            raise ValueError(
                f"<convert-json-to-csv> input must be a JSON array of objects, "
                f"got {type(data).__name__}"
            )

        if not data:
            return FEmptyVariable()

        # flatten nested objects — nested.field becomes "nested.field"
        flat_data = [self._flatten(row) for row in data]

        # get all unique keys preserving order
        keys: list[str] = []
        for row in flat_data:
            for key in row:
                if key not in keys:
                    keys.append(key)

        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=keys,
            delimiter=delimiter,
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(flat_data)

        return FNodeVariable(output.getvalue())

    def _flatten(self, obj: dict, prefix: str = "") -> dict:
        """Flatten nested objects using dot notation."""
        result = {}
        for key, value in obj.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                result.update(self._flatten(value, full_key))
            else:
                result[full_key] = value if value is not None else ""
        return result
