"""
hands/core/record_save_metadata.py

RecordSaveMetadataHand implements the <record-save-metadata> tag.
Registers a path for private metadata JSON — no rows, no duplication.

The JSON file is written once after the session ends (see FRuntime._persist_private_record_metadata)
so status, fin, and duration match the final session, not a mid-workflow snapshot.

Usage in XML:
    <record-save-metadata from="propiedadesRecords"
                          path="output/internal/propiedades_metadata.json"/>
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FEmptyVariable
from francis_suite.core.records import FRecord
from francis_suite.core.expressions import FrancisExpression
from francis_suite.hands.base import AbstractHand


@hand(tag="record-save-metadata")
class RecordSaveMetadataHand(AbstractHand):
    """
    Registers a custom output path for private metadata JSON (no rows).

    The file is written in FRuntime._persist_private_metadata after the session
    completes or fails (same moment as sessions/<session_id>/<record>_private_metadata.json),
    so status, fin, and duracion_segundos are final.

    The runtime also writes private metadata at session end for each FRecord under
    sessions/<session_id>/ (unless FRANCIS_AUTO_RECORD_METADATA=0).

    Missing values in the JSON are null where not applicable, never raises.

    Private metadata includes:
        Traceability:  session_id, workflow_path, francis_suite_version,
                       hostname, sistema_operativo, python_version,
                       status, error, inicio, fin
        Performance:   duracion_segundos, ram_peak_mb, ram_promedio_mb,
                       rows_por_segundo, requests_http_total (future),
                       requests_http_fallidas (future)
        Data quality:  total_rows, rows_completados, rows_con_campos_vacios,
                       rows_fallidos, campos_nulos_total, porcentaje_completitud
        Scraping:      paginas_procesadas, paginas_fallidas, urls_visitadas,
                       proxies_usados (future), captchas_encontrados (future),
                       rate_limits_alcanzados (future)
        Extra:         any fields added with <record-private-metadata>

    Attributes:
        from (required): name of the record collection.
        path (required): output file path. Supports ${variables}.

    Returns:
        FEmptyVariable always.

    Examples:
        <record-save-metadata from="propiedadesRecords"
                              path="output/internal/propiedades_metadata.json"/>

        <!-- with dynamic path -->
        <record-save-metadata from="propiedadesRecords"
                              path="output/internal/metadata_${session_id}.json"/>
    """

    def execute(self) -> FVariable:
        engine      = FrancisExpression(self.context)
        record_name = engine.resolve(self.require_attr("from"))
        path        = engine.resolve(self.require_attr("path"))

        record = self.context.get_shared_box(record_name)

        if not isinstance(record, FRecord):
            raise ValueError(
                f"[RECORD] record '{record_name}' not found. "
                f"Make sure <record-create name=\"{record_name}\"> runs first."
            )

        record.register_deferred_private_metadata_path(path)
        return FEmptyVariable()
