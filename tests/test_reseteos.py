"""Pruebas para reconocer los reseteos confirmados por ADManager."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reporte_bot.lector_logs import EventoLog
from reporte_bot.reseteos import extraer_reseteo_exitoso


def crear_evento(fecha_utc: str, mensaje: str) -> EventoLog:
    """Crea un evento breve para expresar cada caso de prueba."""
    return EventoLog(
        fecha_utc=fecha_utc,
        nivel="INFO",
        operation_id="operacion-1",
        mensaje=mensaje,
    )


class ReseteosTests(unittest.TestCase):
    """Comprueba cuándo una operación merece aparecer en el reporte."""

    def test_extrae_los_datos_de_un_reseteo_exitoso(self) -> None:
        eventos = [
            crear_evento(
                "2026-08-29T12:00:00Z",
                "HTTP Request: http://bot/resetuser?"
                "sAMAccountName_requester=administrador&"
                "sAMAccountName_target=usuario-objetivo",
            ),
            crear_evento(
                "2026-08-29T12:00:05Z",
                "ADM-Raw response | body: [{'sAMAccountName': "
                "'usuario-confirmado', 'reset': 'yes', "
                "'statusMessage': 'Password reset successful.', 'status': '1'}]",
            ),
        ]

        reseteo = extraer_reseteo_exitoso(eventos, "2026-08-29.log")

        self.assertIsNotNone(reseteo)
        assert reseteo is not None
        self.assertEqual(reseteo.operation_id, "operacion-1")
        self.assertEqual(reseteo.fecha_solicitud_utc, "2026-08-29T12:00:00Z")
        self.assertEqual(reseteo.fecha_reseteo_utc, "2026-08-29T12:00:05Z")
        self.assertEqual(reseteo.usuario_solicitante, "administrador")
        self.assertEqual(reseteo.usuario_reseteado, "usuario-confirmado")
        self.assertEqual(reseteo.estado, "exitoso")
        self.assertEqual(reseteo.archivo_origen, "2026-08-29.log")

    def test_ignora_una_respuesta_con_error_de_admanager(self) -> None:
        eventos = [
            crear_evento(
                "2026-08-29T12:00:00Z",
                "HTTP Request: http://bot/resetuser?"
                "sAMAccountName_requester=administrador",
            ),
            crear_evento(
                "2026-08-29T12:00:05Z",
                "ADM-Raw response | status: 500 | error inesperado",
            ),
        ]

        reseteo = extraer_reseteo_exitoso(eventos, "2026-08-29.log")

        self.assertIsNone(reseteo)

    def test_ignora_una_operacion_sin_confirmacion(self) -> None:
        eventos = [
            crear_evento(
                "2026-08-29T12:00:00Z",
                "HTTP Request: http://bot/resetuser?"
                "sAMAccountName_requester=administrador",
            )
        ]

        reseteo = extraer_reseteo_exitoso(eventos, "2026-08-29.log")

        self.assertIsNone(reseteo)
