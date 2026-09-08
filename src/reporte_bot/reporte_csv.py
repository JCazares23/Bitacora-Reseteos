"""Escritura del reporte CSV sin repetir operaciones ya registradas."""

import csv
from collections.abc import Iterable
from dataclasses import asdict
from pathlib import Path

from reporte_bot.reseteos import ReseteoExitoso

COLUMNAS_REPORTE = (
    "operation_id",
    "fecha_solicitud_utc",
    "fecha_reseteo_utc",
    "usuario_solicitante",
    "usuario_reseteado",
    "estado",
    "archivo_origen",
)


def actualizar_reporte(
    ruta_csv: str | Path, reseteos: Iterable[ReseteoExitoso]
) -> int:
    """Agrega solo reseteos nuevos y devuelve cuántas filas escribió."""
    ruta = Path(ruta_csv)
    operation_ids_existentes = _leer_operation_ids(ruta)
    reseteos_nuevos: list[ReseteoExitoso] = []

    for reseteo in reseteos:
        if reseteo.operation_id not in operation_ids_existentes:
            reseteos_nuevos.append(reseteo)
            operation_ids_existentes.add(reseteo.operation_id)

    debe_escribir_encabezado = not ruta.exists() or ruta.stat().st_size == 0
    if not reseteos_nuevos and not debe_escribir_encabezado:
        return 0

    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("a", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=COLUMNAS_REPORTE)
        if debe_escribir_encabezado:
            escritor.writeheader()
        escritor.writerows(asdict(reseteo) for reseteo in reseteos_nuevos)

    return len(reseteos_nuevos)


def _leer_operation_ids(ruta_csv: Path) -> set[str]:
    """Lee las operaciones ya guardadas para no escribirlas otra vez."""
    if not ruta_csv.exists() or ruta_csv.stat().st_size == 0:
        return set()

    with ruta_csv.open(newline="", encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo)
        return {
            fila["operation_id"]
            for fila in lector
            if fila.get("operation_id")
        }
