"""
hands/core/record_private_metadata.py

RecordPrivateMetadataHand implements the <record-private-metadata> tag.
Adds custom fields to the private metadata of a record collection.

Can be placed anywhere in the workflow — not just inside record-create.
Use it to track scraping-specific data like pages processed, URLs visited, etc.

Usage in XML:
    <record-private-metadata to="propiedadesRecords">
        <private-metadata-add-field name="paginas_procesadas">${i}</private-metadata-add-field>
        <private-metadata-add-field name="ultima_url">${url_actual}</private-metadata-add-field>
        <private-metadata-add-field name="portal">Portal Inmobiliario</private-metadata-add-field>
    </record-private-metadata>
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FEmptyVariable
from francis_suite.core.records import FRecord
from francis_suite.core.expressions import FrancisExpression
from francis_suite.hands.base import AbstractHand


@hand(tag="record-private-metadata")
class RecordPrivateMetadataHand(AbstractHand):
    """
    Adds custom fields to the private metadata of a record collection.
    Can be used anywhere in the workflow.

    Fields added here appear in record-save-meta output under their own names.
    They are never included in the public output from record-save.

    Common use cases:
        - paginas_procesadas — track pages scraped
        - paginas_fallidas   — track failed pages
        - urls_visitadas     — track URLs visited
        - ultima_url         — track current URL for debugging
        - portal             — source portal name

    Attributes:
        to (required): name of the record collection to add metadata to.

    Child tags:
        <private-metadata-add-field name="...">value or ${variable}</private-metadata-add-field>

    Returns:
        FEmptyVariable always.

    Example:
        <!-- inside a loop — update metadata as scraping progresses -->
        <loop item="pagina" index="i">
            <loop-body>
                <!-- scraping... -->
                <record-private-metadata to="propiedadesRecords">
                    <private-metadata-add-field name="paginas_procesadas">${i}</private-metadata-add-field>
                    <private-metadata-add-field name="ultima_url">${url}</private-metadata-add-field>
                </record-private-metadata>
            </loop-body>
        </loop>
    """

    def execute(self) -> FVariable:
        engine      = FrancisExpression(self.context)
        record_name = engine.resolve(self.require_attr("to"))

        record = self.context.get_shared_box(record_name)

        if not isinstance(record, FRecord):
            raise ValueError(
                f"[RECORD] record '{record_name}' not found. "
                f"Make sure <record-create name=\"{record_name}\"> runs first."
            )

        for field_node in self.node.children:
            if field_node.tag != "private-metadata-add-field":
                continue

            field_name  = field_node.require_attr("name")
            field_value = engine.resolve(field_node.text or "")
            record.add_private_metadata(field_name, field_value)

        return FEmptyVariable()
