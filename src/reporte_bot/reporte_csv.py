"""Escritura del reporte CSV sin repetir filas ya registradas."""

import csv
from collections.abc import Iterable
from pathlib import Path

from reporte_bot.resetuser import COLUMNAS_REPORTE, RegistroResetUser


def actualizar_reporte(
    ruta_csv: str | Path, registros: Iterable[RegistroResetUser]
) -> int:
    """Agrega solo filas nuevas y devuelve cuantas escribio."""
    ruta = Path(ruta_csv)
    claves_existentes = _leer_claves(ruta)
    registros_nuevos: list[RegistroResetUser] = []

    for registro in registros:
        clave = _crear_clave(registro.como_fila())
        if clave not in claves_existentes:
            registros_nuevos.append(registro)
            claves_existentes.add(clave)

    debe_escribir_encabezado = not ruta.exists() or ruta.stat().st_size == 0
    if not registros_nuevos and not debe_escribir_encabezado:
        return 0

    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("a", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=COLUMNAS_REPORTE)
        if debe_escribir_encabezado:
            escritor.writeheader()
        escritor.writerows(registro.como_fila() for registro in registros_nuevos)

    return len(registros_nuevos)


def _leer_claves(ruta_csv: Path) -> set[tuple[str, ...]]:
    """Lee las filas existentes para no escribirlas otra vez."""
    if not ruta_csv.exists() or ruta_csv.stat().st_size == 0:
        return set()

    with ruta_csv.open(newline="", encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo)
        if tuple(lector.fieldnames or ()) != COLUMNAS_REPORTE:
            raise ValueError(
                "El CSV existente usa un encabezado anterior. "
                "Eliminelo y vuelva a procesar los logs."
            )
        return {_crear_clave(fila) for fila in lector}


def _crear_clave(fila: dict[str, str | None]) -> tuple[str, ...]:
    """Usa todos los campos del reporte como identificador de una fila."""
    return tuple(fila.get(columna) or "" for columna in COLUMNAS_REPORTE)
