"""Pruebas para obtener perfiles desde respuestas de ADManager."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reporte_bot.admanager import obtener_usuarios
from reporte_bot.lector_logs import EventoLog


class ADManagerTests(unittest.TestCase):
    """Comprueba que se extraigan los datos necesarios del perfil."""

    def test_extrae_nombre_oficina_y_reglas_del_usuario(self) -> None:
        eventos = [
            EventoLog(
                fecha_utc="2026-08-29T12:00:00Z",
                nivel="INFO",
                operation_id="operacion-1",
                mensaje="HTTP Request: GET SearchUser?filter="
                "%28sAMAccountName%3Aequal%3Aadministrador%29",
            ),
            EventoLog(
                fecha_utc="2026-08-29T12:00:01Z",
                nivel="INFO",
                operation_id="operacion-1",
                mensaje="Raw Response: {\"UsersList\":[{"
                "\"FIRST_NAME\":\"Ana\",\"LAST_NAME\":\"López\","
                "\"SAM_ACCOUNT_NAME\":\"Administrador\","
                "\"OFFICE\":\"001\","
                "\"DESCRIPTION\":\"Administrador de sistemas\","
                "\"OU_NAME\":\"OAT/Tiendas\"}]}",
            ),
        ]

        usuarios = obtener_usuarios(eventos)

        usuario = usuarios["administrador"]
        self.assertEqual(usuario.nombre_completo, "Ana López")
        self.assertEqual(usuario.oficina, "001")
        self.assertEqual(usuario.descripcion, "Administrador de sistemas")
