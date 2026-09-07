"""Gestión del estado de sesión del estudiante en Streamlit."""

import re

import streamlit as st


ESTUDIANTE_INICIAL = {
    "nombre": "No registrado",
    "correo": "No registrado",
}


def inicializar_estado() -> None:
    if "estudiante" not in st.session_state:
        st.session_state.estudiante = ESTUDIANTE_INICIAL.copy()

    if "mensajes" not in st.session_state:
        st.session_state.mensajes = []


def actualizar_estado_estudiante(texto: str) -> None:
    """Detecta nombre y correo del estudiante en el texto recibido.

    Guarda únicamente el primer nombre del estudiante, sin apellidos.
    """
    texto_limpio = texto.strip()

    # 1. Frases explícitas: "soy X", "me llamo X", "mi nombre es X", "nombre: X"
    patron_nombre = r"(?:soy|me llamo|mi nombre es|nombre:?)\s+([A-Za-zÁÉÍÓÚáéíóúÑñ]+)"
    coincidencia_nombre = re.search(patron_nombre, texto_limpio, re.IGNORECASE)

    if coincidencia_nombre:
        primer_nombre = coincidencia_nombre.group(1)
        st.session_state.estudiante["nombre"] = primer_nombre.capitalize()

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

    # Detecta el correo en cualquier parte del mensaje
    patron_correo = r"[\w\.-]+@[\w\.-]+\.\w+"
    coincidencia_correo = re.search(patron_correo, texto_limpio)
    if coincidencia_correo:
        st.session_state.estudiante["correo"] = coincidencia_correo.group(0)


def agregar_mensaje(role: str, content: str) -> None:
    st.session_state.mensajes.append({"role": role, "content": content})



def obtener_memoria(limite: int = 6) -> str:
    mensajes = st.session_state.mensajes[-limite:]
    return "\n".join(f"{m['role']}: {m['content']}" for m in mensajes)



def reiniciar_estado() -> None:
    st.session_state.mensajes = []
    st.session_state.estudiante = ESTUDIANTE_INICIAL.copy()