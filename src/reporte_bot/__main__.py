"""Comando para procesar el log de una fecha."""

import argparse
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from reporte_bot.pipeline import procesar_archivo

RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
NOMBRE_REPORTE = "tabla_reporte_bot.csv"


def main(argumentos: Sequence[str] | None = None) -> int:
    """Procesa el log indicado y muestra cuántas filas nuevas agregó."""
    parser = argparse.ArgumentParser(
        description="Genera el reporte de reseteos para una fecha."
    )
    parser.add_argument(
        "--fecha",
        required=True,
        help="Fecha del log en formato AAAA-MM-DD.",
    )
    argumentos_leidos = parser.parse_args(argumentos)

    try:
        fecha = date.fromisoformat(argumentos_leidos.fecha)
    except ValueError:
        parser.error("--fecha debe tener el formato AAAA-MM-DD.")

    ruta_log = RAIZ_PROYECTO / "data" / "raw" / f"{fecha.isoformat()}.log"
    if not ruta_log.is_file():
        parser.error(f"No se encontró el log: {ruta_log.name}")

    ruta_csv = RAIZ_PROYECTO / "data" / "output" / NOMBRE_REPORTE
    filas_nuevas = procesar_archivo(ruta_log, ruta_csv)
    print(f"{ruta_log.name}: {filas_nuevas} filas nuevas en {NOMBRE_REPORTE}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
