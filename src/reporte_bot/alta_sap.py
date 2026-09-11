"""Reglas del endpoint ``users_admin/alta_sap``."""

import re
from collections.abc import Iterable
from dataclasses import dataclass

from reporte_bot.admanager import UsuarioADManager, obtener_usuarios
from reporte_bot.lector_logs import EventoLog
from reporte_bot.texto import normalizar

RUTA_ALTA_SAP = "/users_admin/alta_sap?"
PATRON_SOLICITANTE = re.compile(r"sAMAccountName_requester=(?P<valor>[^&\s\"]+)")
PATRON_TARGET = re.compile(r"employeeID_target=(?P<valor>[^&\s\"]+)")
PATRON_CODIGO = re.compile(r'HTTP/1\.1"? (?P<codigo>\d{3})')


@dataclass(frozen=True)
class RegistroAltaSap:
    """Representa una fila del reporte para una solicitud de alta SAP."""

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
            "accion": "alta de usuario",
            "sistema": "SAP",
            "nombre completo del usuario solicitante": self.nombre_solicitante,
            "nombre completo del usuario target": self.nombre_target,
            "oficina del usuario solicitante": self.oficina_solicitante,
            "oficina del usuario target": self.oficina_target,
            "resultado": self.resultado,
        }


def extraer_registro(eventos: Iterable[EventoLog]) -> RegistroAltaSap | None:
    """Construye una fila para una operacion de alta SAP encontrada en el log."""
    eventos_lista = list(eventos)
    solicitud = next(
        (evento for evento in eventos_lista if RUTA_ALTA_SAP in evento.mensaje), None
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
    return RegistroAltaSap(
        timestamp=solicitud.fecha_utc,
        solicitante=solicitante,
        target=target,
        nombre_solicitante=_nombre(usuario_solicitante),
        nombre_target=_nombre(usuario_target),
        oficina_solicitante=_oficina(usuario_solicitante),
        oficina_target=_oficina(usuario_target),
        resultado=_crear_resultado(codigo, usuario_solicitante, usuario_target),
    )


def _crear_resultado(
    codigo: str,
    solicitante: UsuarioADManager | None,
    target: UsuarioADManager | None,
) -> str:
    """Traduce los status codes de Alta SAP definidos en la especificacion."""
    if codigo == "200":
        return (
            "El usuario objetivo fue registrado en SAP, el ticket control se creo "
            "y se cerro."
        )
    if codigo == "202":
        return (
            "El usuario objetivo fue registrado en SAP, pero no se pudo crear o "
            "cerrar el ticket control."
        )
    if codigo == "208":
        return "El usuario objetivo ya existe en el ambiente ECC/ECP de SAP."
    if codigo == "400":
        return (
            "El alta no paso las validaciones: employee ID, tratamiento o puesto "
            "solicitado no es valido."
        )
    if codigo == "401":
        return "El usuario solicitante no es gerente ni administrador de sistemas."
    if codigo == "403":
        if solicitante and normalizar(solicitante.corporativo) == "oat":
            return (
                "El usuario solicitante es de OAT y no tiene permitido ejecutar "
                "el alta SAP."
            )
        if solicitante and target and solicitante.oficina != target.oficina:
            return "Los usuarios no pertenecen a la misma oficina."
        return "El alta fue rechazada por una regla de permisos."
    if codigo == "404":
        if not solicitante and not target:
            return "No se encontro el usuario solicitante ni el usuario objetivo."
        if not solicitante:
            return "El usuario solicitante no se encontro en ADManager."
        return "El usuario objetivo no se encontro en ADManager."
    if codigo == "500":
        return "Ocurrio un error desconocido al procesar el alta SAP."
    if codigo == "503":
        return "Las validaciones fueron exitosas, pero el servicio de SAP fallo."
    return f"El alta SAP termino con un resultado no reconocido: {codigo}."


def _valor(patron: re.Pattern[str], texto: str) -> str | None:
    coincidencia = patron.search(texto)
    if not coincidencia:
        return None
    if "valor" in coincidencia.groupdict():
        return coincidencia["valor"]
    return coincidencia["codigo"]


def _nombre(usuario: UsuarioADManager | None) -> str:
    return usuario.nombre_completo if usuario else ""


def _oficina(usuario: UsuarioADManager | None) -> str:
    return usuario.oficina if usuario else ""
