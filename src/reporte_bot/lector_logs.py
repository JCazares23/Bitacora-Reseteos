"""Funciones para entender los eventos que deja el bot en sus logs."""

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

PATRON_EVENTO = re.compile(
    r"^(?P<fecha_utc>\S+) \| (?P<nivel>\w+) "
    r"\[operation_Id=(?P<operation_id>[^\]]+)\] \| (?P<mensaje>.*)$"
)


@dataclass(frozen=True)
class EventoLog:
    """Representa un mensaje del log asociado a una operación del bot."""

    fecha_utc: str
    nivel: str
    operation_id: str
    mensaje: str


def leer_eventos(ruta: str | Path) -> list[EventoLog]:
    """Lee un log y devuelve los eventos asociados a una operación.

    Algunas respuestas de ADManager continúan en la línea siguiente. Esas
    líneas se unen al mensaje anterior para no perder información.
    """
    eventos: list[EventoLog] = []
    evento_actual: dict[str, str] | None = None

    with Path(ruta).open(encoding="utf-8") as archivo:
        for linea in archivo:
            texto = linea.rstrip("\r\n")
            coincidencia = PATRON_EVENTO.match(texto)

            if coincidencia:
                if evento_actual:
                    eventos.append(EventoLog(**evento_actual))

                evento_actual = {
                    "fecha_utc": coincidencia["fecha_utc"],
                    "nivel": coincidencia["nivel"],
                    "operation_id": coincidencia["operation_id"],
                    "mensaje": coincidencia["mensaje"],
                }
            elif evento_actual:
                evento_actual["mensaje"] += f"\n{texto}"

    if evento_actual:
        eventos.append(EventoLog(**evento_actual))

    return eventos


def agrupar_por_operacion(
    eventos: Iterable[EventoLog],
) -> dict[str, list[EventoLog]]:
    """Reúne los eventos de cada operación sin cambiar su orden original."""
    operaciones: dict[str, list[EventoLog]] = {}

    for evento in eventos:
        operaciones.setdefault(evento.operation_id, []).append(evento)

    return operaciones
