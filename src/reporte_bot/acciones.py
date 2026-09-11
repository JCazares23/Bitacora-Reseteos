"""Registro pequeno de las acciones que el reporte sabe procesar."""

from collections.abc import Callable, Iterable

from reporte_bot.alta_sap import RUTA_ALTA_SAP, RegistroAltaSap
from reporte_bot.alta_sap import extraer_registro as extraer_alta_sap
from reporte_bot.lector_logs import EventoLog
from reporte_bot.resetuser import RegistroResetUser, extraer_registro

ProcesadorAccion = Callable[
    [Iterable[EventoLog]], RegistroResetUser | RegistroAltaSap | None
]

ACCIONES_SOPORTADAS: dict[str, ProcesadorAccion] = {
    "/users_admin/resetuser?": extraer_registro,
    RUTA_ALTA_SAP: extraer_alta_sap,
}


def procesar_operacion(eventos: Iterable[EventoLog]) -> RegistroResetUser | None:
    """Busca una accion registrada y crea su fila para el reporte."""
    eventos_lista = list(eventos)

    for ruta, procesador in ACCIONES_SOPORTADAS.items():
        if any(ruta in evento.mensaje for evento in eventos_lista):
            return procesador(eventos_lista)

    return None
