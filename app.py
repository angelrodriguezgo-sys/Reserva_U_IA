"""Interfaz principal del Asistente de Reserva de Espacios con Streamlit + LangChain.

Este módulo configura y ejecuta la interfaz web del asistente. Gestiona
la visualización de los datos del estudiante, el historial de
conversación, el detalle de la última ejecución (ruta tomada por el
router y herramientas usadas) y la interacción entre el usuario y el
agente basado en Gemini + LangChain.
"""

import streamlit as st

from config.settings import validar_configuracion
from core.agent import responder
from core.state import (
    agregar_mensaje,
    actualizar_estado_estudiante,
    inicializar_estado,
    obtener_memoria,
    registrar_ejecucion,
    reiniciar_estado,
)


st.set_page_config(
    page_title="Reserva de Espacios",
    page_icon="🏫",
)


# Valida que las variables necesarias para utilizar Gemini estén configuradas.
try:
    validar_configuracion()
except ValueError as error:
    st.error(str(error))
    st.stop()


# Inicializa el estado persistente de la sesión de Streamlit.
inicializar_estado()


# Encabezado principal de la aplicación.
st.title("Asistente de Reserva de Espacios")
st.caption("Universidad Católica Luis Amigó")
st.write(
    "Consulta espacios disponibles, reserva salas y revisa tus reservas. "
    "Con LangChain: Chain de enrutamiento, Agent y múltiples Tools."
)


# Panel lateral: datos del estudiante y detalle de la última ejecución.
with st.sidebar:
    st.subheader("Datos del estudiante")

    estudiante = st.session_state.estudiante
    st.write("Nombre:", estudiante["nombre"])
    st.write("Correo:", estudiante["correo"])

    st.divider()
    st.subheader("Última ejecución")

    ejecucion = st.session_state.ultima_ejecucion
    st.write("Ruta:", ejecucion["ruta"])

    if ejecucion["motivo"]:
        st.caption(ejecucion["motivo"])

    if ejecucion["tools"]:
        st.write("Tools utilizadas:")
        for nombre in ejecucion["tools"]:
            st.write(f"- {nombre}")
    else:
        st.write("Tools utilizadas: ninguna")

    st.divider()

    if st.button("Reiniciar conversación"):
        reiniciar_estado()
        st.rerun()


# Renderiza el historial de mensajes almacenados en la sesión.
for mensaje in st.session_state.mensajes:
    with st.chat_message(mensaje["role"]):
        st.markdown(mensaje["content"])


# Captura una nueva consulta del estudiante.
prompt = st.chat_input("Escribe tu solicitud (ej. reservar un espacio, consultar disponibilidad)...")

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)

    actualizar_estado_estudiante(prompt)
    agregar_mensaje("user", prompt)

    try:
        resultado = responder(
            mensaje_usuario=prompt,
            estudiante=st.session_state.estudiante,
            memoria=obtener_memoria(),
        )
        respuesta = resultado["respuesta"]
        registrar_ejecucion(resultado)

    except Exception as error:
        respuesta = f"Ocurrió un error al procesar la solicitud: {error}"
        resultado = None

    with st.chat_message("assistant"):
        st.markdown(respuesta)

        if resultado and resultado.get("reserva_exitosa"):
            st.success("✅ ¡Reserva realizada con éxito!")
            st.balloons()

    agregar_mensaje("assistant", respuesta)
    
    st.rerun()