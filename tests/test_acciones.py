"""Pruebas del registro de acciones soportadas por el reporte."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reporte_bot.acciones import procesar_operacion
from reporte_bot.lector_logs import EventoLog


class AccionesTests(unittest.TestCase):
    """Comprueba que solo se procesen acciones registradas."""

    def test_ignora_una_accion_que_no_esta_registrada(self) -> None:
        eventos = [
            EventoLog(
                fecha_utc="2026-09-01T12:00:00Z",
                nivel="INFO",
                operation_id="operacion-1",
                mensaje="HTTP Request: http://bot/users_admin/otra_accion",
            )
        ]

        self.assertIsNone(procesar_operacion(eventos))
