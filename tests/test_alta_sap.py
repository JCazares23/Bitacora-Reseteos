"""Pruebas de las reglas de resultado para Alta SAP."""

import sys
import unittest
from json import dumps
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reporte_bot.alta_sap import extraer_registro
from reporte_bot.lector_logs import EventoLog


def crear_eventos(codigo: str) -> list[EventoLog]:
    """Crea una operacion minima de alta SAP."""
    return [
        EventoLog(
            fecha_utc="2026-08-29T12:00:00Z",
            nivel="INFO",
            operation_id="operacion-sap",
            mensaje=(
                "HTTP Request: http://bot/users_admin/alta_sap?"
                "sAMAccountName_requester=administrador&"
                "employeeID_target=12345 "
                f"HTTP/1.1 {codigo}"
            ),
        )
    ]


def crear_perfil(
    usuario: str,
    campo_busqueda: str,
    oficina: str = "001",
    corporativo: str = "",
) -> list[EventoLog]:
    """Crea una busqueda y respuesta de ADManager para un usuario."""
    respuesta = {
        "UsersList": [
            {
                "FIRST_NAME": "Nombre",
                "LAST_NAME": usuario,
                "SAM_ACCOUNT_NAME": usuario,
                "OFFICE": oficina,
                "DESCRIPTION": "Administrador",
                "OU_NAME": "OAT/Tiendas",
                "CORPORATIVO": corporativo,
            }
        ]
    }
    return [
        EventoLog(
            fecha_utc="2026-08-29T12:00:01Z",
            nivel="INFO",
            operation_id="operacion-sap",
            mensaje=(
                "HTTP Request: GET SearchUser?filter=%28"
                f"{campo_busqueda}%3Aequal%3A{usuario}%29"
            ),
        ),
        EventoLog(
            fecha_utc="2026-08-29T12:00:02Z",
            nivel="INFO",
            operation_id="operacion-sap",
            mensaje=f"Raw Response: {dumps(respuesta)}",
        ),
    ]


class AltaSapTests(unittest.TestCase):
    """Comprueba los mensajes definidos en StatusCodes Alta SAP V2."""

    def test_crea_una_fila_de_alta_sap_exitosa(self) -> None:
        registro = extraer_registro(crear_eventos("200"))

        assert registro is not None
        self.assertEqual(registro.como_fila()["accion"], "alta de usuario")
        self.assertEqual(registro.como_fila()["sistema"], "SAP")
        self.assertIn("ticket control", registro.resultado)

    def test_traduce_los_status_codes_generales(self) -> None:
        casos = {
            "202": "crear o cerrar",
            "208": "ya existe",
            "400": "validaciones",
            "401": "gerente",
            "500": "desconocido",
            "503": "servicio de SAP fallo",
        }

        for codigo, esperado in casos.items():
            with self.subTest(codigo=codigo):
                registro = extraer_registro(crear_eventos(codigo))
                assert registro is not None
                self.assertIn(esperado, registro.resultado)

    def test_403_explica_solicitante_de_oat(self) -> None:
        eventos = crear_eventos("403")
        eventos += crear_perfil("administrador", "sAMAccountName", corporativo="OAT")

        registro = extraer_registro(eventos)

        assert registro is not None
        self.assertIn("OAT", registro.resultado)

    def test_403_explica_oficinas_distintas(self) -> None:
        eventos = crear_eventos("403")
        eventos += crear_perfil("administrador", "sAMAccountName")
        eventos += crear_perfil("12345", "employeeID", oficina="002")

        registro = extraer_registro(eventos)

        assert registro is not None
        self.assertIn("misma oficina", registro.resultado)

    def test_404_distingue_el_usuario_objetivo_ausente(self) -> None:
        eventos = crear_eventos("404")
        eventos += crear_perfil("administrador", "sAMAccountName")

        registro = extraer_registro(eventos)

        assert registro is not None
        self.assertIn("objetivo", registro.resultado)
