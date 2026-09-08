"""Orquestación del proceso completo para un archivo de log."""

from pathlib import Path

from reporte_bot.lector_logs import agrupar_por_operacion, leer_eventos
from reporte_bot.reporte_csv import actualizar_reporte
from reporte_bot.reseteos import extraer_reseteo_exitoso


def procesar_archivo(ruta_log: str | Path, ruta_csv: str | Path) -> int:
    """Procesa un log y guarda los reseteos nuevos en el reporte."""
    ruta = Path(ruta_log)
    operaciones = agrupar_por_operacion(leer_eventos(ruta))
    reseteos = []

    for eventos in operaciones.values():
        reseteo = extraer_reseteo_exitoso(eventos, ruta.name)
        if reseteo:
            reseteos.append(reseteo)

    return actualizar_reporte(ruta_csv, reseteos)
