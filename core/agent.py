"""Núcleo del Asistente de Reserva de Espacios con LangChain.

Decide si una solicitud se resuelve mediante una Chain determinista
(respuestas generales) o mediante un Agent con múltiples Tools (cuando
se necesita consultar disponibilidad, reservar, o cualquier acción que
requiera datos dinámicos).
"""

from typing import TypedDict

import ast
import json

from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from chains.response_chain import crear_respuesta_chain
from chains.router_chain import crear_router_chain
from config.settings import GEMINI_API_KEY, GEMINI_MODEL
from prompts.academic_prompt import AGENT_SYSTEM_TEMPLATE
from tools.eventos_campus_tool import consultar_eventos_campus
from tools.fecha_tool import obtener_fecha, resolver_fecha_relativa
from tools.horario_tool import (
    consultar_espacios_disponibles,
    consultar_horarios_disponibles_dia,
    consultar_mis_reservas,
    generar_calendario_mes,
    reservar_espacio,
)
from tools.recomendacion_tool import recomendar_espacio


class Estudiante(TypedDict):
    """Representa la información básica de un estudiante."""

    nombre: str
    correo: str


TOOLS = [
    obtener_fecha,
    resolver_fecha_relativa,
    consultar_espacios_disponibles,
    reservar_espacio,
    consultar_mis_reservas,
    generar_calendario_mes,
    consultar_horarios_disponibles_dia,
    consultar_eventos_campus,
    recomendar_espacio,
]


def _crear_modelo() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        api_key=GEMINI_API_KEY,
        temperature=0.1,
    )


def _construir_system_prompt(estudiante: Estudiante, memoria: str) -> str:
    return AGENT_SYSTEM_TEMPLATE.format(
        nombre=estudiante["nombre"],
        correo=estudiante["correo"],
        memoria=memoria or "Sin memoria reciente.",
    )


def _extraer_texto_final(result: dict) -> str:
    """Extrae el contenido textual del último mensaje del Agent."""
    mensajes = result.get("messages", [])

    if not mensajes:
        return "No fue posible generar una respuesta."

    contenido = mensajes[-1].content

    if isinstance(contenido, str):
        return contenido

    if isinstance(contenido, list):
        partes = []
        for bloque in contenido:
            if isinstance(bloque, dict) and bloque.get("type") == "text":
                partes.append(str(bloque.get("text", "")))
            elif isinstance(bloque, str):
                partes.append(bloque)
        texto = "\n".join(p for p in partes if p).strip()
        return texto or "No fue posible generar una respuesta."

    return str(contenido)


def _detectar_tools_usadas(result: dict) -> list[str]:
    """Obtiene nombres de Tools solicitadas por el modelo."""
    usadas: list[str] = []

    for mensaje in result.get("messages", []):
        tool_calls = getattr(mensaje, "tool_calls", None) or []
        for call in tool_calls:
            nombre = call.get("name")
            if nombre and nombre not in usadas:
                usadas.append(nombre)

    return usadas

def _detectar_reserva_exitosa(result: dict) -> bool:
    """Revisa si la tool reservar_espacio fue invocada y devolvió éxito.

    Busca en los mensajes del Agent el resultado de la tool
    ``reservar_espacio`` e interpreta su contenido (dict o string) para
    verificar la clave ``exito``.
    """
    for mensaje in result.get("messages", []):
        if getattr(mensaje, "name", None) != "reservar_espacio":
            continue

        contenido = mensaje.content

        if isinstance(contenido, dict):
            return contenido.get("exito") is True

        if isinstance(contenido, str):
            texto = contenido.strip()
            for parser in (json.loads, ast.literal_eval):
                try:
                    datos = parser(texto)
                    if isinstance(datos, dict):
                        return datos.get("exito") is True
                except (ValueError, SyntaxError):
                    continue

    return False

def responder(mensaje_usuario: str, estudiante: Estudiante, memoria: str) -> dict:
    """Responde mediante Chain o Agent según la naturaleza de la consulta."""
    router = crear_router_chain()
    decision = router.invoke({"pregunta": mensaje_usuario})

    if decision.ruta == "chain":
        chain = crear_respuesta_chain()
        texto = chain.invoke({"pregunta": mensaje_usuario})

        return {
            "respuesta": texto,
            "ruta": "Chain",
            "motivo": decision.motivo,
            "tools": [],
            "reserva_exitosa": False,
        }

    model = _crear_modelo()

    agent = create_agent(
        model=model,
        tools=TOOLS,
        system_prompt=_construir_system_prompt(
            estudiante=estudiante,
            memoria=memoria,
        ),
    )

    result = agent.invoke(
        {"messages": [{"role": "user", "content": mensaje_usuario}]}
    )

    return {
        "respuesta": _extraer_texto_final(result),
        "ruta": "Agent",
        "motivo": decision.motivo,
        "tools": _detectar_tools_usadas(result),
        "reserva_exitosa": _detectar_reserva_exitosa(result),
    }