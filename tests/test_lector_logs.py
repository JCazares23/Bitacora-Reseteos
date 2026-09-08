"""Pruebas que confirman como se leen y agrupan los logs."""

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reporte_bot.lector_logs import agrupar_por_operacion, leer_eventos


class LectorLogsTests(unittest.TestCase):
    """Comprueba el comportamiento basico del lector de logs."""

    def test_lee_y_agrupa_eventos_de_la_misma_operacion(self) -> None:
        contenido = (
            "2026-08-29T12:00:00Z | INFO [operation_Id=operacion-a] | "
            "solicitud inicial\n"
            "detalle adicional de la solicitud\n"
            "2026-08-29T12:00:01Z | INFO [operation_Id=operacion-b] | "
            "otra solicitud\n"
            "2026-08-29T12:00:02Z | ERROR [operation_Id=operacion-a] | "
            "respuesta final\n"
        )

        with TemporaryDirectory() as directorio:
            ruta_log = Path(directorio) / "ejemplo.log"
            ruta_log.write_text(contenido, encoding="utf-8")

            eventos = leer_eventos(ruta_log)

        operaciones = agrupar_por_operacion(eventos)

        self.assertEqual(len(eventos), 3)
        self.assertEqual(eventos[0].fecha_utc, "2026-08-29T12:00:00Z")
        self.assertEqual(eventos[0].nivel, "INFO")
        self.assertEqual(
            eventos[0].mensaje,
            "solicitud inicial\ndetalle adicional de la solicitud",
        )
        self.assertEqual(list(operaciones), ["operacion-a", "operacion-b"])
        self.assertEqual(len(operaciones["operacion-a"]), 2)
        self.assertEqual(operaciones["operacion-a"][1].nivel, "ERROR")
