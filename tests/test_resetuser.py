"""Pruebas de las reglas de resultado para el endpoint resetuser."""

import sys
import unittest
from json import dumps
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


def crear_perfil(
    usuario: str,
    oficina: str = "001",
    descripcion: str = "Administrador",
    ou_name: str = "OAT/Tiendas",
) -> list[EventoLog]:
    """Crea la busqueda y la respuesta de ADManager para un usuario."""
    respuesta = {
        "UsersList": [
            {
                "FIRST_NAME": "Nombre",
                "LAST_NAME": usuario,
                "SAM_ACCOUNT_NAME": usuario,
                "OFFICE": oficina,
                "DESCRIPTION": descripcion,
                "OU_NAME": ou_name,
            }
        ]
    }
    return [
        EventoLog(
            fecha_utc="2026-08-29T12:00:01Z",
            nivel="INFO",
            operation_id="operacion-1",
            mensaje="HTTP Request: GET SearchUser?filter="
            f"%28sAMAccountName%3Aequal%3A{usuario}%29",
        ),
        EventoLog(
            fecha_utc="2026-08-29T12:00:02Z",
            nivel="INFO",
            operation_id="operacion-1",
            mensaje=f"Raw Response: {dumps(respuesta)}",
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

    def test_403_explica_oficinas_distintas(self) -> None:
        eventos = crear_eventos("403") + crear_perfil("administrador")
        eventos += crear_perfil("usuario", oficina="002")

        registro = extraer_registro(eventos)

        assert registro is not None
        self.assertIn("misma oficina", registro.resultado)

    def test_403_explica_solicitante_sin_permiso(self) -> None:
        eventos = crear_eventos("403")
        eventos += crear_perfil("administrador", descripcion="Empleado")
        eventos += crear_perfil("usuario")

        registro = extraer_registro(eventos)

        assert registro is not None
        self.assertIn("no tiene permisos", registro.resultado)

    def test_403_explica_ou_restringida(self) -> None:
        eventos = crear_eventos("403")
        eventos += crear_perfil("administrador", descripcion="Gerente")
        eventos += crear_perfil("usuario", ou_name="OAT/Cedis/BY")

        registro = extraer_registro(eventos)

        assert registro is not None
        self.assertIn("OAT/Cedis/BY", registro.resultado)

    def test_404_explica_cuando_no_existe_ningun_usuario(self) -> None:
        registro = extraer_registro(crear_eventos("404"))

        assert registro is not None
        self.assertIn("Ningun usuario", registro.resultado)

    def test_404_explica_cuando_no_existe_el_solicitante(self) -> None:
        eventos = crear_eventos("404") + crear_perfil("usuario")

        registro = extraer_registro(eventos)

        assert registro is not None
        self.assertIn("solicitante no se encontro", registro.resultado)

    def test_404_explica_cuando_no_existe_el_usuario_objetivo(self) -> None:
        eventos = crear_eventos("404") + crear_perfil("administrador")

        registro = extraer_registro(eventos)

        assert registro is not None
        self.assertIn("objetivo no se encontro", registro.resultado)
