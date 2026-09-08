"""Pruebas para guardar el reporte con el contrato final."""

import csv
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reporte_bot.reporte_csv import actualizar_reporte
from reporte_bot.resetuser import RegistroResetUser


def crear_registro(timestamp: str) -> RegistroResetUser:
    """Crea una fila breve para probar la idempotencia del CSV."""
    return RegistroResetUser(
        timestamp=timestamp,
        solicitante="administrador",
        target="usuario",
        nombre_solicitante="Ana López",
        nombre_target="Luis Pérez",
        oficina_solicitante="001",
        oficina_target="001",
        resultado="El reseteo de contraseña se realizó correctamente en ADManager.",
    )


class ReporteCsvTests(unittest.TestCase):
    """Comprueba que el CSV conserva una sola fila por operación."""

    def test_agrega_solo_filas_nuevas(self) -> None:
        primer_registro = crear_registro("2026-08-29T12:00:00Z")
        segundo_registro = crear_registro("2026-08-29T12:01:00Z")

        with TemporaryDirectory() as directorio:
            ruta_csv = Path(directorio) / "reporte.csv"
            primera_ejecucion = actualizar_reporte(ruta_csv, [primer_registro])
            segunda_ejecucion = actualizar_reporte(
                ruta_csv, [primer_registro, segundo_registro]
            )

            with ruta_csv.open(newline="", encoding="utf-8") as archivo:
                filas = list(csv.DictReader(archivo))

        self.assertEqual(primera_ejecucion, 1)
        self.assertEqual(segunda_ejecucion, 1)
        self.assertEqual(len(filas), 2)
        self.assertEqual(filas[0]["acción"], "reseteo de contraseña")
        self.assertEqual(filas[0]["resultado"], primer_registro.resultado)
