"""Gestión del estado de sesión y memoria del estudiante en Streamlit.

Este módulo administra la información básica del estudiante, el historial
de mensajes y el detalle de la última ejecución del agente, almacenados
en ``st.session_state``.

También incluye utilidades para identificar el nombre y el correo del
estudiante a partir de texto libre, construir una memoria reciente de la
conversación y reiniciar el estado de la sesión.
"""

import re

import streamlit as st


# Estado inicial utilizado cuando aún no se ha identificado al estudiante.
ESTUDIANTE_INICIAL = {
    "nombre": "No registrado",
    "correo": "No registrado",
}

# Estado inicial del detalle de la última ejecución del agente.
EJECUCION_INICIAL = {
    "ruta": "N/A",
    "motivo": "",
    "tools": [],
}


def inicializar_estado() -> None:
    """Inicializa las variables necesarias en el estado de sesión.

    Crea la información inicial del estudiante, el historial de mensajes
    y el detalle de la última ejecución, únicamente cuando dichas variables
    aún no existen en ``st.session_state``.

    Esto permite conservar la información entre las distintas ejecuciones
    de la aplicación Streamlit dentro de una misma sesión.
    """
    if "estudiante" not in st.session_state:
        st.session_state.estudiante = ESTUDIANTE_INICIAL.copy()

    if "mensajes" not in st.session_state:
        st.session_state.mensajes = []

    if "ultima_ejecucion" not in st.session_state:
        st.session_state.ultima_ejecucion = EJECUCION_INICIAL.copy()


def actualizar_estado_estudiante(texto: str) -> None:
    """Detecta nombre y correo del estudiante en el texto recibido.

    Guarda únicamente el primer nombre del estudiante, sin apellidos.
    """
    texto_limpio = texto.strip()

    # 1. Frases explícitas: "soy X", "me llamo X", "mi nombre es X", "nombre: X"
    patron_nombre = r"(?:soy|me llamo|mi nombre es|nombre:?)\s+([A-Za-zÁÉÍÓÚáéíóúÑñ]+)"
    coincidencia_nombre = re.search(patron_nombre, texto_limpio, re.IGNORECASE)

    if coincidencia_nombre:
        st.session_state.estudiante["nombre"] = coincidencia_nombre.group(1).capitalize()

    # 2. Si aún no hay nombre registrado y el estudiante escribió solo su nombre
    #    (sin correo, sin números, y como máximo un par de palabras), se asume
    #    que esa respuesta es directamente el nombre.
    elif (
        st.session_state.estudiante["nombre"] == "No registrado"
        and "@" not in texto_limpio
        and re.fullmatch(
            r"[A-Za-zÁÉÍÓÚáéíóúÑñ]+(?:\s+[A-Za-zÁÉÍÓÚáéíóúÑñ]+){0,2}",
            texto_limpio,
        )
    ):
        primer_nombre = texto_limpio.split()[0]
        st.session_state.estudiante["nombre"] = primer_nombre.capitalize()

    # Detecta el correo en cualquier parte del mensaje.
    patron_correo = r"[\w\.-]+@[\w\.-]+\.\w+"
    coincidencia_correo = re.search(patron_correo, texto_limpio)
    if coincidencia_correo:
        st.session_state.estudiante["correo"] = coincidencia_correo.group(0)


def agregar_mensaje(role: str, content: str) -> None:
    """Agrega un mensaje al historial de conversación de la sesión.

    Args:
        role: Rol asociado al mensaje, por ejemplo ``"user"`` o
            ``"assistant"``.
        content: Contenido textual del mensaje que se desea almacenar.
    """
    st.session_state.mensajes.append(
        {
            "role": role,
            "content": content,
        }
    )


def registrar_ejecucion(resultado: dict) -> None:
    """Guarda en la sesión la información de la última ejecución del agente.

    Args:
        resultado: Diccionario devuelto por ``core.agent.responder``, con
            las claves ``ruta``, ``motivo`` y ``tools``.
    """
    st.session_state.ultima_ejecucion = {
        "ruta": resultado.get("ruta", "N/A"),
        "motivo": resultado.get("motivo", ""),
        "tools": resultado.get("tools", []),
    }


def obtener_memoria(limite: int = 6) -> str:
    """Construye una representación textual de los mensajes recientes.

    Recupera los últimos mensajes almacenados en la sesión y los convierte
    en una cadena de texto que puede utilizarse como contexto o memoria
    conversacional.

    Args:
        limite: Número máximo de mensajes recientes que se incluirán.
            Por defecto se utilizan los últimos 6 mensajes.

    Returns:
        Cadena con los mensajes recientes en formato ``"role: content"``,
        separados por saltos de línea. Devuelve una cadena vacía si no
        existen mensajes almacenados.
    """
    mensajes = st.session_state.mensajes[-limite:]

    return "\n".join(
        f"{mensaje['role']}: {mensaje['content']}"
        for mensaje in mensajes
    )


def reiniciar_estado() -> None:
    """Restablece la información de la sesión a sus valores iniciales.

    Elimina el historial de conversación, reemplaza la información del
    estudiante por una nueva copia de ``ESTUDIANTE_INICIAL`` y reinicia
    el detalle de la última ejecución.
    """
    st.session_state.mensajes = []
    st.session_state.estudiante = ESTUDIANTE_INICIAL.copy()
    st.session_state.ultima_ejecucion = EJECUCION_INICIAL.copy()