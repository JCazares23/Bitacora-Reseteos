"""Pruebas para guardar el reporte sin repetir operaciones."""

import csv
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reporte_bot.reporte_csv import actualizar_reporte
from reporte_bot.reseteos import ReseteoExitoso


def crear_reseteo(operation_id: str) -> ReseteoExitoso:
    """Crea un reseteo pequeño para probar la escritura del CSV."""
    return ReseteoExitoso(
        operation_id=operation_id,
        fecha_solicitud_utc="2026-08-29T12:00:00Z",
        fecha_reseteo_utc="2026-08-29T12:00:05Z",
        usuario_solicitante="administrador",
        usuario_reseteado="usuario",
        estado="exitoso",
        archivo_origen="2026-08-29.log",
    )


class ReporteCsvTests(unittest.TestCase):
    """Comprueba que el CSV conserva una sola fila por operación."""

    def test_agrega_solo_operaciones_nuevas(self) -> None:
        primer_reseteo = crear_reseteo("operacion-1")
        segundo_reseteo = crear_reseteo("operacion-2")

        with TemporaryDirectory() as directorio:
            ruta_csv = Path(directorio) / "reporte.csv"

            filas_primera_ejecucion = actualizar_reporte(
                ruta_csv, [primer_reseteo]
            )
            filas_segunda_ejecucion = actualizar_reporte(
                ruta_csv, [primer_reseteo, segundo_reseteo]
            )

            with ruta_csv.open(newline="", encoding="utf-8") as archivo:
                filas = list(csv.DictReader(archivo))

        self.assertEqual(filas_primera_ejecucion, 1)
        self.assertEqual(filas_segunda_ejecucion, 1)
        self.assertEqual([fila["operation_id"] for fila in filas], [
            "operacion-1",
            "operacion-2",
        ])
