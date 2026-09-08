"""Reglas para reconocer reseteos confirmados por ADManager."""

import re
from collections.abc import Iterable
from dataclasses import dataclass

from reporte_bot.lector_logs import EventoLog

PATRON_SOLICITANTE = re.compile(
    r"sAMAccountName_requester=(?P<usuario>[^&\s\"]+)"
)
PATRON_USUARIO_RESETEADO = re.compile(
    r"['\"]sAMAccountName['\"]:\s*['\"](?P<usuario>[^'\"]+)['\"]"
)
MARCAS_DE_EXITO = (
    "'reset': 'yes'",
    "'statusMessage': 'Password reset successful.'",
    "'status': '1'",
)


@dataclass(frozen=True)
class ReseteoExitoso:
    """Contiene los datos mínimos de un reseteo confirmado."""

    operation_id: str
    fecha_solicitud_utc: str
    fecha_reseteo_utc: str
    usuario_solicitante: str
    usuario_reseteado: str
    estado: str
    archivo_origen: str


def extraer_reseteo_exitoso(
    eventos: Iterable[EventoLog], archivo_origen: str
) -> ReseteoExitoso | None:
    """Devuelve el reseteo si ADManager lo confirmó; si no, devuelve nada."""
    solicitud: EventoLog | None = None
    usuario_solicitante: str | None = None

    for evento in eventos:
        if "/resetuser?" in evento.mensaje:
            coincidencia = PATRON_SOLICITANTE.search(evento.mensaje)
            if coincidencia:
                solicitud = evento
                usuario_solicitante = coincidencia["usuario"]

        if all(marca in evento.mensaje for marca in MARCAS_DE_EXITO):
            coincidencia = PATRON_USUARIO_RESETEADO.search(evento.mensaje)
            if solicitud and usuario_solicitante and coincidencia:
                return ReseteoExitoso(
                    operation_id=evento.operation_id,
                    fecha_solicitud_utc=solicitud.fecha_utc,
                    fecha_reseteo_utc=evento.fecha_utc,
                    usuario_solicitante=usuario_solicitante,
                    usuario_reseteado=coincidencia["usuario"],
                    estado="exitoso",
                    archivo_origen=archivo_origen,
                )

    return None
