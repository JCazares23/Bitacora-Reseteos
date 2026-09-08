"""Reglas del endpoint ``users_admin/resetuser``."""

import re
from collections.abc import Iterable
from dataclasses import dataclass

from reporte_bot.admanager import UsuarioADManager, obtener_usuarios
from reporte_bot.lector_logs import EventoLog
from reporte_bot.texto import normalizar

PATRON_SOLICITANTE = re.compile(r"sAMAccountName_requester=(?P<usuario>[^&\s\"]+)")
PATRON_TARGET = re.compile(r"sAMAccountName_target=(?P<usuario>[^&\s\"]+)")
PATRON_CODIGO = re.compile(r'HTTP/1\.1"? (?P<codigo>\d{3})')
PATRON_MENSAJE_ADMANAGER = re.compile(r"'statusMessage': '(?P<mensaje>[^']*)'")

COLUMNAS_REPORTE = (
    "timestamp",
    "solicitante",
    "target",
    "accion",
    "sistema",
    "nombre completo del usuario solicitante",
    "nombre completo del usuario target",
    "oficina del usuario solicitante",
    "oficina del usuario target",
    "resultado",
)


@dataclass(frozen=True)
class RegistroResetUser:
    """Representa una fila completa del reporte de reseteos."""

    timestamp: str
    solicitante: str
    target: str
    nombre_solicitante: str
    nombre_target: str
    oficina_solicitante: str
    oficina_target: str
    resultado: str

    def como_fila(self) -> dict[str, str]:
        """Entrega la fila con los nombres exactos acordados para el CSV."""
        return {
            "timestamp": self.timestamp,
            "solicitante": self.solicitante,
            "target": self.target,
            "accion": "reseteo de contrasena",
            "sistema": "ADManager",
            "nombre completo del usuario solicitante": self.nombre_solicitante,
            "nombre completo del usuario target": self.nombre_target,
            "oficina del usuario solicitante": self.oficina_solicitante,
            "oficina del usuario target": self.oficina_target,
            "resultado": self.resultado,
        }


def extraer_registro(eventos: Iterable[EventoLog]) -> RegistroResetUser | None:
    """Construye una fila para una operacion de reseteo encontrada en el log."""
    eventos_lista = list(eventos)
    solicitud = next(
        (
            evento
            for evento in eventos_lista
            if "/users_admin/resetuser?" in evento.mensaje
        ),
        None,
    )
    if solicitud is None:
        return None

    solicitante = _valor(PATRON_SOLICITANTE, solicitud.mensaje)
    target = _valor(PATRON_TARGET, solicitud.mensaje)
    codigo = _valor(PATRON_CODIGO, solicitud.mensaje)
    if not solicitante or not target or not codigo:
        return None

    usuarios = obtener_usuarios(eventos_lista)
    usuario_solicitante = usuarios.get(normalizar(solicitante))
    usuario_target = usuarios.get(normalizar(target))

    return RegistroResetUser(
        timestamp=solicitud.fecha_utc,
        solicitante=solicitante,
        target=target,
        nombre_solicitante=_nombre(usuario_solicitante),
        nombre_target=_nombre(usuario_target),
        oficina_solicitante=_oficina(usuario_solicitante),
        oficina_target=_oficina(usuario_target),
        resultado=_crear_resultado(
            codigo, usuario_solicitante, usuario_target, eventos_lista
        ),
    )


def _crear_resultado(
    codigo: str,
    solicitante: UsuarioADManager | None,
    target: UsuarioADManager | None,
    eventos: Iterable[EventoLog],
) -> str:
    """Traduce el codigo y los datos de ADManager a un mensaje util."""
    if codigo == "200":
        return "El reseteo de contrasena se realizo correctamente en ADManager."
    if codigo == "202":
        return (
            "El usuario objetivo pertenece a Corporativo y no puede resetearse "
            "mediante el bot."
        )
    if codigo == "403":
        if solicitante and target and solicitante.oficina != target.oficina:
            return "Los usuarios no pertenecen a la misma oficina."
        if solicitante and not normalizar(solicitante.descripcion).startswith(
            ("gerente", "admin")
        ):
            return "El usuario solicitante no tiene permisos para realizar el reseteo."
        if target and normalizar(target.ou_name) == "oat/cedis/by":
            return "El usuario objetivo pertenece a OAT/Cedis/BY y no puede resetearse."
        return "El reseteo fue rechazado por una regla de permisos."
    if codigo == "404":
        if not solicitante and not target:
            return "Ningun usuario se encontro en ADManager."
        if not solicitante:
            return "El usuario solicitante no se encontro en ADManager."
        return "El usuario objetivo no se encontro en ADManager."
    if codigo == "429":
        return (
            "No se pudo ejecutar el reseteo porque se agotaron los tokens de "
            "ADManager."
        )
    if codigo == "500":
        return "Ocurrio un error interno inesperado al procesar el reseteo."
    if codigo == "503":
        detalle = _mensaje_admanager(eventos)
        if detalle:
            return f"ADManager no pudo ejecutar el reseteo: {detalle}"
        return "ADManager no pudo ejecutar el reseteo."
    if codigo == "504":
        return "La comunicacion con ADManager excedio el tiempo de espera."
    return f"El reseteo termino con un resultado no reconocido: {codigo}."


def _valor(patron: re.Pattern[str], texto: str) -> str | None:
    """Obtiene un valor nombrado de una expresion regular."""
    coincidencia = patron.search(texto)
    if not coincidencia:
        return None
    if "usuario" in coincidencia.groupdict():
        return coincidencia["usuario"]
    return coincidencia["codigo"]


def _nombre(usuario: UsuarioADManager | None) -> str:
    """Devuelve el nombre completo o una cadena vacia si no existe perfil."""
    return usuario.nombre_completo if usuario else ""


def _oficina(usuario: UsuarioADManager | None) -> str:
    """Devuelve la oficina o una cadena vacia si no existe perfil."""
    return usuario.oficina if usuario else ""


def _mensaje_admanager(eventos: Iterable[EventoLog]) -> str | None:
    """Obtiene el detalle exacto que ADManager devolvio en un error 503."""
    for evento in eventos:
        if "ADM-Raw response" in evento.mensaje:
            coincidencia = PATRON_MENSAJE_ADMANAGER.search(evento.mensaje)
            if coincidencia:
                return coincidencia["mensaje"]
    return None
