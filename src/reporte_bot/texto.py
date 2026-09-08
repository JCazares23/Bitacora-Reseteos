"""Utilidades pequenas para comparar texto inconsistente de ADManager."""

import unicodedata


def normalizar(valor: str) -> str:
    """Quita acentos y mayusculas para comparar textos sin sorpresas."""
    sin_acentos = unicodedata.normalize("NFD", valor)
    sin_acentos = "".join(
        caracter
        for caracter in sin_acentos
        if unicodedata.category(caracter) != "Mn"
    )
    return sin_acentos.casefold().strip()
