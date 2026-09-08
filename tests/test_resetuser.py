"""Pruebas de las reglas de resultado para el endpoint resetuser."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reporte_bot.lector_logs import EventoLog
from reporte_bot.resetuser import extraer_registro


def crear_eventos(codigo: str, detalle: str = "") -> list[EventoLog]:
    """Crea una operacion minima para probar cada resultado."""
    return [
        EventoLog(
            fecha_utc="2026-08-29T12:00:00Z",
            nivel="INFO",
            operation_id="operacion-1",
            mensaje="HTTP Request: http://bot/users_admin/resetuser?"
            "sAMAccountName_requester=administrador&"
            "sAMAccountName_target=usuario "
            f"HTTP/1.1 {codigo}",
        ),
        EventoLog(
            fecha_utc="2026-08-29T12:00:01Z",
            nivel="INFO",
            operation_id="operacion-1",
            mensaje=detalle,
        ),
    ]


class ResetUserTests(unittest.TestCase):
    """Comprueba los mensajes informativos de cada codigo del endpoint."""

    def test_crea_las_columnas_de_un_reseteo_exitoso(self) -> None:
        registro = extraer_registro(crear_eventos("200"))

        assert registro is not None
        fila = registro.como_fila()
        self.assertEqual(fila["timestamp"], "2026-08-29T12:00:00Z")
        self.assertEqual(fila["accion"], "reseteo de contrasena")
        self.assertIn("correctamente", fila["resultado"])

    def test_traduce_los_codigos_generales_a_mensajes_humanos(self) -> None:
        casos = {
            "202": "Corporativo",
            "429": "agotaron los tokens",
            "500": "error interno inesperado",
            "504": "tiempo de espera",
        }

        for codigo, esperado in casos.items():
            with self.subTest(codigo=codigo):
                registro = extraer_registro(crear_eventos(codigo))
                assert registro is not None
                self.assertIn(esperado, registro.resultado)

    def test_conserva_el_detalle_de_admanager_en_un_error_503(self) -> None:
        detalle = (
            "ADM-Raw response | body: [{'statusMessage': 'No such user matched', "
            "'status': '0'}]"
        )

        registro = extraer_registro(crear_eventos("503", detalle))

        assert registro is not None
        self.assertIn("No such user matched", registro.resultado)
