"""Control de acceso de LUXXON: aplicación institucional privada.

Solo se puede usar con un correo institucional (nombre@amigo.edu.co).
Este módulo no depende de Streamlit.
"""

import re
from typing import Optional

# Dominio institucional permitido. También se aceptan sus subdominios
# (por ejemplo, estudiantes.amigo.edu.co). Cámbialo aquí si es otro.
DOMINIO_INSTITUCIONAL = "amigo.edu.co"

PATRON_CORREO = r"[\w\.-]+@[\w\.-]+\.\w+"


def es_correo_institucional(correo: str) -> bool:
    """Indica si el correo tiene el formato nombre@amigo.edu.co."""
    correo = correo.strip().lower()

    if not re.fullmatch(PATRON_CORREO, correo):
        return False

    dominio = correo.rsplit("@", 1)[1]
    return dominio == DOMINIO_INSTITUCIONAL or dominio.endswith(
        "." + DOMINIO_INSTITUCIONAL
    )


def detectar_correo_no_institucional(texto: str) -> Optional[str]:
    """Devuelve el primer correo del texto que no sea institucional, si lo hay."""
    for correo in re.findall(PATRON_CORREO, texto):
        if not es_correo_institucional(correo):
            return correo
    return None


def mensaje_acceso_restringido(correo_rechazado: bool, nombre: str = "") -> str:
    """Mensaje que se muestra mientras no haya un correo institucional registrado.

    Args:
        correo_rechazado: True si el estudiante escribió un correo que no es
            institucional.
        nombre: Nombre ya registrado, o cadena vacía si aún no se conoce.
    """
    ejemplo = f"nombre@{DOMINIO_INSTITUCIONAL}"

    if correo_rechazado:
        return (
            "🔒 **LUXXON es una aplicación institucional privada.** "
            f"Solo puede usarse con un correo institucional (por ejemplo, {ejemplo}), "
            "y el correo que escribiste no pertenece a la institución. "
            "Si tienes uno, escríbelo para comenzar."
        )

    if nombre:
        return (
            f"Gracias, {nombre}. Para continuar necesito tu correo institucional "
            f"({ejemplo})."
        )

    return (
        "¡Hola! Soy **Luxxon**, la IA de reserva de espacios universitarios de la "
        "Universidad Católica Luis Amigó. Puedo mostrarte los espacios disponibles, "
        "reservar salas y revisar tus reservas.\n\n"
        "🔒 Es una **aplicación institucional privada**: para usarla necesito tu "
        f"**nombre** y tu **correo institucional** ({ejemplo})."
    )