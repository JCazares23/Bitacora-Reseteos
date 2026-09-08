"""Prueba del comando que ejecuta el proceso completo."""

import csv
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reporte_bot.__main__ import main

LOG_EXITOSO = (
    "2026-08-29T12:00:00Z | INFO [operation_Id=operacion-1] | "
    "HTTP Request: http://bot/resetuser?"
    "sAMAccountName_requester=administrador&"
    "sAMAccountName_target=usuario-objetivo\n"
    "2026-08-29T12:00:05Z | INFO [operation_Id=operacion-1] | "
    "ADM-Raw response | body: [{'sAMAccountName': 'usuario-confirmado', "
    "'reset': 'yes', 'statusMessage': 'Password reset successful.', "
    "'status': '1'}]\n"
)


class CliTests(unittest.TestCase):
    """Comprueba que el comando conecta todas las piezas del proyecto."""

    def test_procesa_un_log_por_fecha_sin_duplicar_filas(self) -> None:
        with TemporaryDirectory() as directorio:
            raiz = Path(directorio)
            ruta_raw = raiz / "data" / "raw"
            ruta_raw.mkdir(parents=True)
            (ruta_raw / "2026-08-29.log").write_text(LOG_EXITOSO, encoding="utf-8")

            with patch("reporte_bot.__main__.RAIZ_PROYECTO", raiz):
                primer_resultado = main(["--fecha", "2026-08-29"])
                segundo_resultado = main(["--fecha", "2026-08-29"])

            ruta_csv = raiz / "data" / "output" / "tabla_reporte_bot.csv"
            with ruta_csv.open(newline="", encoding="utf-8") as archivo:
                filas = list(csv.DictReader(archivo))

        self.assertEqual(primer_resultado, 0)
        self.assertEqual(segundo_resultado, 0)
        self.assertEqual(len(filas), 1)
        self.assertEqual(filas[0]["operation_id"], "operacion-1")
