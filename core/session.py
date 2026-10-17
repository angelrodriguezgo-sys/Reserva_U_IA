"""Gestión del estado de sesión del estudiante en Streamlit.

Administra los datos del estudiante, el historial de mensajes, el detalle
de la última ejecución del grafo y el identificador de hilo (thread_id)
que usa LangGraph para separar la memoria de cada conversación.
"""

import re
import uuid

import streamlit as st


# Estado inicial utilizado cuando aún no se ha identificado al estudiante.
ESTUDIANTE_INICIAL = {
    "nombre": "No registrado",
    "correo": "No registrado",
}

# Estado inicial del detalle de la última ejecución.
EJECUCION_INICIAL = {
    "ruta": "N/A",
    "motivo": "",
    "tools": [],
}

PATRON_CORREO = r"[\w\.-]+@[\w\.-]+\.\w+"
PATRON_NOMBRE_EXPLICITO = (
    r"(?:soy|me llamo|mi nombre es|nombre:?)\s+([A-Za-zÁÉÍÓÚáéíóúÑñ]+)"
)
PATRON_SOLO_NOMBRE = r"[A-Za-zÁÉÍÓÚáéíóúÑñ]+(?:\s+[A-Za-zÁÉÍÓÚáéíóúÑñ]+){0,2}"


def inicializar_estado() -> None:
    """Crea las variables de sesión que aún no existen."""
    if "estudiante" not in st.session_state:
        st.session_state.estudiante = ESTUDIANTE_INICIAL.copy()

    if "mensajes" not in st.session_state:
        st.session_state.mensajes = []

    if "ultima_ejecucion" not in st.session_state:
        st.session_state.ultima_ejecucion = EJECUCION_INICIAL.copy()

    if "thread_id" not in st.session_state:
        st.session_state.thread_id = uuid.uuid4().hex


def _asistente_pidio_nombre() -> bool:
    """Indica si el último mensaje del asistente preguntaba por el nombre."""
    for mensaje in reversed(st.session_state.mensajes):
        if mensaje["role"] == "assistant":
            return "nombre" in mensaje["content"].lower()
    return False


def actualizar_estado_estudiante(texto: str) -> None:
    """Detecta el correo y el primer nombre del estudiante en el texto."""
    texto_limpio = texto.strip()

    coincidencia_correo = re.search(PATRON_CORREO, texto_limpio)
    if coincidencia_correo:
        st.session_state.estudiante["correo"] = coincidencia_correo.group(0)

    # Texto sin el correo, para detectar el nombre aunque lleguen juntos.
    sin_correo = re.sub(PATRON_CORREO, "", texto_limpio).strip(" ,;:-")

    coincidencia_nombre = re.search(
        PATRON_NOMBRE_EXPLICITO, sin_correo, re.IGNORECASE
    )

    if coincidencia_nombre:
        st.session_state.estudiante["nombre"] = (
            coincidencia_nombre.group(1).capitalize()
        )
    elif (
        st.session_state.estudiante["nombre"] == "No registrado"
        and _asistente_pidio_nombre()
        and "correo" not in sin_correo.lower()
        and re.fullmatch(PATRON_SOLO_NOMBRE, sin_correo)
    ):
        st.session_state.estudiante["nombre"] = sin_correo.split()[0].capitalize()


def agregar_mensaje(role: str, content: str) -> None:
    """Agrega un mensaje al historial de conversación de la sesión."""
    st.session_state.mensajes.append({"role": role, "content": content})


def registrar_ejecucion(resultado: dict) -> None:
    """Guarda ruta, motivo y tools de la última ejecución del grafo."""
    st.session_state.ultima_ejecucion = {
        "ruta": resultado.get("ruta", "N/A"),
        "motivo": resultado.get("motivo", ""),
        "tools": resultado.get("tools", []),
    }


def obtener_memoria(limite: int = 6) -> str:
    """Devuelve los últimos mensajes como texto 'role: content'."""
    mensajes = st.session_state.mensajes[-limite:]

    return "\n".join(
        f"{mensaje['role']}: {mensaje['content']}" for mensaje in mensajes
    )


def reiniciar_estado() -> None:
    """Restablece la sesión y abre un hilo nuevo para el agente.

    Sin un thread_id nuevo, la pantalla se vería limpia pero el agente
    seguiría recordando la conversación anterior.
    """
    st.session_state.mensajes = []
    st.session_state.estudiante = ESTUDIANTE_INICIAL.copy()
    st.session_state.ultima_ejecucion = EJECUCION_INICIAL.copy()
    st.session_state.thread_id = uuid.uuid4().hex
    st.session_state.pop("reserva_confirmada", None)