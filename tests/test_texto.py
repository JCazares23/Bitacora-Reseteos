"""Pruebas para las comparaciones de texto de ADManager."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reporte_bot.texto import normalizar


class TextoTests(unittest.TestCase):
    """Comprueba que acentos y mayusculas no cambien una comparacion."""

    def test_normaliza_acentos_mayusculas_y_espacios(self) -> None:
        self.assertEqual(normalizar("  CORPORATIVO  "), "corporativo")
        self.assertEqual(normalizar("Mexico"), "mexico")
