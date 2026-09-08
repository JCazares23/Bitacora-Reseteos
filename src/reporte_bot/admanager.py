"""Lectura de los perfiles de usuario devueltos por ADManager."""

import json
import re
from collections.abc import Iterable
from dataclasses import dataclass

from reporte_bot.lector_logs import EventoLog
from reporte_bot.texto import normalizar

PATRON_USUARIO_BUSCADO = re.compile(
    r"sAMAccountName(?::equal:|%3Aequal%3A)(?P<usuario>[^)%\s\"]+)"
)


@dataclass(frozen=True)
class UsuarioADManager:
    """Representa los datos del perfil que necesita el reporte."""

    cuenta: str
    nombre_completo: str
    oficina: str
    descripcion: str
    ou_name: str


def obtener_usuarios(eventos: Iterable[EventoLog]) -> dict[str, UsuarioADManager]:
    """Relaciona cada búsqueda de usuario con su respuesta de ADManager."""
    usuarios: dict[str, UsuarioADManager] = {}
    usuario_buscado: str | None = None

    for evento in eventos:
        coincidencia = PATRON_USUARIO_BUSCADO.search(evento.mensaje)
        if "SearchUser" in evento.mensaje and coincidencia:
            usuario_buscado = coincidencia["usuario"]

        respuesta = _extraer_respuesta(evento.mensaje)
        if usuario_buscado and respuesta is not None:
            lista_usuarios = respuesta.get("UsersList", [])
            if lista_usuarios:
                usuarios[normalizar(usuario_buscado)] = _crear_usuario(
                    lista_usuarios[0]
                )
            usuario_buscado = None

    return usuarios


def _extraer_respuesta(mensaje: str) -> dict[str, object] | None:
    """Convierte el JSON que aparece después de ``Raw Response``."""
    if "Raw Response: {" not in mensaje:
        return None

    contenido = mensaje.split("Raw Response: ", maxsplit=1)[1].lstrip()
    try:
        respuesta, _ = json.JSONDecoder().raw_decode(contenido)
    except json.JSONDecodeError:
        return None

    return respuesta if isinstance(respuesta, dict) else None


def _crear_usuario(datos: dict[str, object]) -> UsuarioADManager:
    """Reduce la respuesta extensa de ADManager a los campos del reporte."""
    nombres = str(datos.get("FIRST_NAME", "")).strip()
    apellidos = str(datos.get("LAST_NAME", "")).strip()
    nombre_completo = " ".join(parte for parte in (nombres, apellidos) if parte)
    cuenta = str(datos.get("SAM_ACCOUNT_NAME", ""))

    return UsuarioADManager(
        cuenta=cuenta,
        nombre_completo=nombre_completo,
        oficina=str(datos.get("OFFICE", "")),
        descripcion=str(datos.get("DESCRIPTION", "")),
        ou_name=str(datos.get("OU_NAME", "")),
    )
