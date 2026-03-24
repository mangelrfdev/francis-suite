"""
hands/core/convert_xml_to_csv.py

ConvertXmlToCsvHand implements the <convert-xml-to-csv> tag.
Converts XML content to CSV format.
Each child element of the root becomes a row.
The child element's children become the columns.

Usage in XML:
    <box-def name="csv">
        <convert-xml-to-csv>
            <box name="data_xml"/>
        </convert-xml-to-csv>
    </box-def>

Input XML format:
    <items>
        <item><nombre>Casa</nombre><precio>100000</precio></item>
        <item><nombre>Depto</nombre><precio>80000</precio></item>
    </items>

Output CSV format:
    nombre,precio
    Casa,100000
    Depto,80000
"""

from __future__ import annotations
import csv
import io
from lxml import etree
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FNodeVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand


@hand(tag="convert-xml-to-csv")
class ConvertXmlToCsvHand(AbstractHand):
    """
    Converts XML content to CSV format.
    Each child element of the root becomes a CSV row.
    The tag names of the grandchildren become the column headers.

    Attributes:
        delimiter (optional): CSV delimiter character. Default: ,

    Returns:
        FNodeVariable with the CSV string.
        FEmptyVariable if input is empty or has no rows.

    Raises:
        ValueError if the input is not valid XML.

    Examples:
        <box-def name="csv">
            <convert-xml-to-csv>
                <box name="data_xml"/>
            </convert-xml-to-csv>
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
            root = etree.fromstring(raw.encode("utf-8"))
        except etree.XMLSyntaxError as e:
            raise ValueError(
                f"<convert-xml-to-csv> invalid XML input: {e}"
            ) from e

        rows = []
        keys: list[str] = []

        for child in root:
            row = {}
            for field in child:
                tag = field.tag
                value = field.text or ""
                row[tag] = value.strip()
                if tag not in keys:
                    keys.append(tag)
            rows.append(row)

        if not rows:
            return FEmptyVariable()

        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=keys,
            delimiter=delimiter,
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

        return FNodeVariable(output.getvalue())
