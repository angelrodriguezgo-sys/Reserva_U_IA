"""Gestión del estado de sesión del estudiante en Streamlit.

Administra la cuenta activa del estudiante, las cuentas anteriores de la
misma conversación, el historial de mensajes, el detalle de la última
ejecución del grafo y el thread_id que usa LangGraph.

Cuando alguien inicia con otra cuenta, la anterior se archiva y el
historial completo se conserva: cada mensaje queda marcado con la cuenta
a la que pertenece.
"""

import re
import uuid

import streamlit as st


NO_REGISTRADO = "No registrado"

# Estado inicial utilizado cuando aún no se ha identificado al estudiante.
ESTUDIANTE_INICIAL = {
    "nombre": NO_REGISTRADO,
    "correo": NO_REGISTRADO,
}

# Estado inicial del detalle de la última ejecución.
EJECUCION_INICIAL = {
    "ruta": "N/A",
    "motivo": "",
    "tools": [],
}
from core.acceso import PATRON_CORREO, es_correo_institucional
PATRON_NOMBRE_EXPLICITO = (
    r"(?:soy|me llamo|mi nombre es|nombre:?)\s+([A-Za-zÁÉÍÓÚáéíóúÑñ]+)"
)
PATRON_SOLO_NOMBRE = r"[A-Za-zÁÉÍÓÚáéíóúÑñ]+(?:\s+[A-Za-zÁÉÍÓÚáéíóúÑñ]+){0,2}"
PATRON_CAMBIO_CUENTA = (
    r"(?:otra cuenta|nueva cuenta|cambiar de cuenta|cambio de cuenta|"
    r"otro usuario|ahora soy)"
)


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

    if "cuenta_id" not in st.session_state:
        st.session_state.cuenta_id = 0

    if "cuentas_anteriores" not in st.session_state:
        st.session_state.cuentas_anteriores = []


def _hay_cuenta_activa() -> bool:
    estudiante = st.session_state.estudiante
    return (
        estudiante["nombre"] != NO_REGISTRADO
        or estudiante["correo"] != NO_REGISTRADO
    )

def acceso_permitido() -> bool:
    """True si la cuenta activa tiene un correo institucional registrado."""
    correo = st.session_state.estudiante["correo"]
    return correo != NO_REGISTRADO and es_correo_institucional(correo)

def iniciar_nueva_cuenta() -> bool:
    """Archiva la cuenta activa y deja una cuenta vacía en la misma conversación.

    No borra mensajes. Abre un hilo nuevo para el agente, de modo que el
    contexto de una cuenta no se mezcle con el de otra; el hilo anterior
    queda guardado junto con la cuenta archivada.

    Returns:
        True si se archivó una cuenta; False si no había cuenta activa.
    """
    if not _hay_cuenta_activa():
        return False

    anterior = st.session_state.estudiante
    st.session_state.cuentas_anteriores.append(
        {
            "cuenta_id": st.session_state.cuenta_id,
            "nombre": anterior["nombre"],
            "correo": anterior["correo"],
            "thread_id": st.session_state.thread_id,
        }
    )

    st.session_state.cuenta_id += 1
    st.session_state.estudiante = ESTUDIANTE_INICIAL.copy()
    st.session_state.thread_id = uuid.uuid4().hex
    st.session_state.ultima_ejecucion = EJECUCION_INICIAL.copy()

    # Marcador que la interfaz dibuja como una línea divisoria.
    st.session_state.mensajes.append(
        {
            "role": "cambio_cuenta",
            "content": "🔁 Cambio de cuenta: la conversación anterior queda guardada.",
            "cuenta_id": st.session_state.cuenta_id,
        }
    )
    return True


def _asistente_pidio_nombre() -> bool:
    """Indica si el último mensaje del asistente preguntaba por el nombre."""
    for mensaje in reversed(st.session_state.mensajes):
        if mensaje["role"] == "assistant":
            return "nombre" in mensaje["content"].lower()
    return False


def actualizar_estado_estudiante(texto: str) -> None:
    """Detecta correo y nombre, y cambia de cuenta cuando corresponde.

    Hay cuenta nueva cuando llega un correo distinto al registrado o cuando
    el estudiante lo pide con frases como "otra cuenta". Si solo cambia el
    nombre y el correo es el mismo, se trata como una corrección.
    """
    texto_limpio = texto.strip()

    coincidencia_correo = re.search(PATRON_CORREO, texto_limpio)
    correo_nuevo = coincidencia_correo.group(0) if coincidencia_correo else None

    # Texto sin el correo, para detectar el nombre aunque lleguen juntos.
    sin_correo = re.sub(PATRON_CORREO, "", texto_limpio).strip(" ,;:-")
    quiere_cambiar = bool(re.search(PATRON_CAMBIO_CUENTA, texto_limpio.lower()))

    correo_actual = st.session_state.estudiante["correo"]
    correo_distinto = (
        correo_nuevo is not None
        and correo_actual != NO_REGISTRADO
        and correo_nuevo.lower() != correo_actual.lower()
    )
    correo_igual = (
        correo_nuevo is not None and correo_nuevo.lower() == correo_actual.lower()
    )

    if correo_distinto or (quiere_cambiar and not correo_igual):
        iniciar_nueva_cuenta()

    estudiante = st.session_state.estudiante

    if correo_nuevo:
        estudiante["correo"] = correo_nuevo

    coincidencia_nombre = re.search(
        PATRON_NOMBRE_EXPLICITO, sin_correo, re.IGNORECASE
    )

    if coincidencia_nombre:
        estudiante["nombre"] = coincidencia_nombre.group(1).capitalize()
    elif (
        estudiante["nombre"] == NO_REGISTRADO
        and _asistente_pidio_nombre()
        and "correo" not in sin_correo.lower()
        and re.fullmatch(PATRON_SOLO_NOMBRE, sin_correo)
    ):
        estudiante["nombre"] = sin_correo.split()[0].capitalize()


def agregar_mensaje(role: str, content: str) -> None:
    """Agrega un mensaje al historial, marcado con la cuenta activa."""
    st.session_state.mensajes.append(
        {
            "role": role,
            "content": content,
            "cuenta_id": st.session_state.cuenta_id,
        }
    )


def registrar_ejecucion(resultado: dict) -> None:
    """Guarda ruta, motivo y tools de la última ejecución del grafo."""
    st.session_state.ultima_ejecucion = {
        "ruta": resultado.get("ruta", "N/A"),
        "motivo": resultado.get("motivo", ""),
        "tools": resultado.get("tools", []),
    }


def obtener_memoria(limite: int = 6) -> str:
    """Devuelve los últimos mensajes de la cuenta activa como 'role: content'.

    Solo incluye mensajes de la cuenta actual, para que el agente no mezcle
    datos de una persona con los de otra.
    """
    mensajes = [
        mensaje
        for mensaje in st.session_state.mensajes
        if mensaje["role"] in ("user", "assistant")
        and mensaje.get("cuenta_id", 0) == st.session_state.cuenta_id
    ]

    return "\n".join(
        f"{mensaje['role']}: {mensaje['content']}" for mensaje in mensajes[-limite:]
    )


def reiniciar_estado() -> None:
    """Restablece toda la sesión (incluidas las cuentas archivadas).

    Es el botón de reinicio total. Para conservar el historial al cambiar
    de persona, se usa iniciar_nueva_cuenta().
    """
    st.session_state.mensajes = []
    st.session_state.estudiante = ESTUDIANTE_INICIAL.copy()
    st.session_state.ultima_ejecucion = EJECUCION_INICIAL.copy()
    st.session_state.thread_id = uuid.uuid4().hex
    st.session_state.cuenta_id = 0
    st.session_state.cuentas_anteriores = []
    st.session_state.pop("reserva_confirmada", None)