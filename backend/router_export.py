"""
Endpoint per l'export del piano operativo in formato Excel.
"""

from __future__ import annotations

import io

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import StreamingResponse

from . import session_store

router = APIRouter(prefix="/api", tags=["export"])


@router.get("/export")
def export_excel(
    x_session_id: str = Header(..., alias="X-Session-ID"),
) -> StreamingResponse:
    """
    Genera ed esporta il piano operativo corrente come file Excel.
    Richiede che /api/elabora sia già stato chiamato nella stessa sessione.
    """
    sess = session_store.get(x_session_id)

    if sess is None or sess.risultato_df is None:
        raise HTTPException(
            status_code=404,
            detail="Nessun risultato disponibile. Eseguire prima l'elaborazione.",
        )

    df = sess.risultato_df

    # Rinomina colonne per leggibilità nel file Excel
    df_export = df.rename(columns={
        "LOTTO": "Lotto",
        "COD_ARTICOLO": "Cod. Articolo",
        "DESCRIZIONE_ARTICOLO": "Descrizione",
        "COD_PDV": "Cod. PDV",
        "NOME_PDV": "Nome PDV",
        "GIORNI_RESIDUI": "Giorni Residui",
        "INDICE_ROT": "Indice Rotazione",
        "CAPACITA_STIMATA": "Capacità Stimata",
        "QTA_PROPOSTA": "Qta Proposta",
        "PRIORITA": "Priorità",
        "MOTIVO": "Motivo",
        "MODALITA_CALCOLO": "Modalità Calcolo",
    })

    # Scrivi in buffer in memoria
    buffer = io.BytesIO()
    with __import__("pandas").ExcelWriter(buffer, engine="openpyxl") as writer:
        df_export.to_excel(writer, index=False, sheet_name="Piano Operativo")

        # Aggiusta larghezza colonne automaticamente
        ws = writer.sheets["Piano Operativo"]
        for col_cells in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col_cells)
            ws.column_dimensions[col_cells[0].column_letter].width = min(max_len + 2, 40)

    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=piano_operativo.xlsx"},
    )
