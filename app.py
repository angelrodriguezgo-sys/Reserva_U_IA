"""Luxxon: IA de reserva de espacios universitarios (Streamlit + LangGraph).

Aplicación institucional privada: solo se usa con correo institucional.
Muestra los datos del estudiante, el historial de conversación (con las
cuentas anteriores guardadas) y el detalle de la última ejecución, y conecta
la entrada del usuario con el grafo.
"""

import streamlit as st

from config.settings import validar_configuracion
from core.acceso import detectar_correo_no_institucional, mensaje_acceso_restringido
from core.estilos import CARGANDO_HTML, EXITO_HTML, aplicar_estilos
from core.session import (
    NO_REGISTRADO,
    acceso_permitido,
    actualizar_estado_estudiante,
    agregar_mensaje,
    iniciar_nueva_cuenta,
    inicializar_estado,
    obtener_memoria,
    registrar_ejecucion,
    reiniciar_estado,
)
from graph.workflow import responder


# Debe ser el primer comando de Streamlit.
st.set_page_config(
    page_title="Luxxon",
    page_icon="🔶",
)

aplicar_estilos()


# Valida que las variables necesarias para utilizar Gemini estén configuradas.
try:
    validar_configuracion()
except ValueError as error:
    st.error(str(error))
    st.stop()


# Inicializa el estado persistente de la sesión de Streamlit.
inicializar_estado()


# Encabezado y bienvenida.
st.markdown('<div class="lx-marca">Luxxon</div>', unsafe_allow_html=True)
st.title("IA de reserva de espacios universitarios")
st.caption("Universidad Católica Luis Amigó")
st.write("Consulta espacios disponibles, reserva salas y revisa tus reservas.")


# Panel lateral: cuenta activa, última ejecución y cuentas anteriores.
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

    if st.button("Iniciar con otra cuenta"):
        if iniciar_nueva_cuenta():
            agregar_mensaje(
                "assistant",
                "Listo, guardé la conversación y los datos de la cuenta anterior. "
                "Escribe tu nombre y tu correo institucional para continuar "
                "con la nueva cuenta.",
            )
            st.rerun()
        else:
            st.warning("Aún no hay una cuenta activa para guardar.")

    if st.session_state.cuentas_anteriores:
        st.subheader("Cuentas anteriores")
        for cuenta in st.session_state.cuentas_anteriores:
            st.write(f"- {cuenta['nombre']} ({cuenta['correo']})")

    st.divider()

    if st.button("Reiniciar conversación"):
        reiniciar_estado()
        st.rerun()


# Historial de mensajes, con una línea divisoria en cada cambio de cuenta.
for mensaje in st.session_state.mensajes:
    if mensaje["role"] == "cambio_cuenta":
        st.divider()
        st.caption(mensaje["content"])
        continue

    with st.chat_message(mensaje["role"]):
        st.markdown(mensaje["content"])


# Alerta de reserva exitosa: se muestra después del rerun para que no se borre.
if st.session_state.pop("reserva_confirmada", False):
    st.markdown(EXITO_HTML, unsafe_allow_html=True)
    st.balloons()


# Nueva consulta del estudiante.
prompt = st.chat_input(
    "Escribe tu solicitud (ej. reservar un espacio, consultar disponibilidad)..."
)

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)

    # Un correo que no sea institucional no se registra (ver core/acceso.py).
    correo_rechazado = detectar_correo_no_institucional(prompt)

    # Puede archivar la cuenta activa si el mensaje trae un correo distinto
    # o pide cambiar de cuenta; por eso va antes de guardar el mensaje.
    actualizar_estado_estudiante(prompt)
    agregar_mensaje("user", prompt)

    if correo_rechazado or not acceso_permitido():
        # Sin correo institucional no se llama al agente: es una app privada.
        nombre = st.session_state.estudiante["nombre"]
        respuesta = mensaje_acceso_restringido(
            correo_rechazado=correo_rechazado is not None,
            nombre="" if nombre == NO_REGISTRADO else nombre,
        )
    else:
        with st.chat_message("assistant"):
            # La animación de figuras se muestra mientras el grafo responde.
            cargando = st.empty()
            cargando.markdown(CARGANDO_HTML, unsafe_allow_html=True)

            try:
                resultado = responder(
                    mensaje_usuario=prompt,
                    estudiante=st.session_state.estudiante,
                    memoria=obtener_memoria(),
                    thread_id=st.session_state.thread_id,
                )
                respuesta = resultado["respuesta"]
                registrar_ejecucion(resultado)

                if resultado.get("reserva_exitosa"):
                    st.session_state.reserva_confirmada = True

            except Exception as error:
                respuesta = f"Ocurrió un error al procesar la solicitud: {error}"

            cargando.empty()

    agregar_mensaje("assistant", respuesta)
    st.rerun()