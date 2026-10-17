"""Nodos del grafo del Asistente de Reserva de Espacios.

Nodos:
1. enrutador_node: clasifica la consulta (conceptual / herramientas).
2. conceptual_node: responde dudas generales, sin herramientas.
3. agente_reservas_node: razona con las tools vinculadas.
4. herramientas_node: ejecuta las tools solicitadas con ToolNode.
"""

import ast
import json
from functools import lru_cache
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field

from config.settings import GEMINI_API_KEY, GEMINI_MODEL
from graph.state import ReservaState
from prompts.academic_prompt import (
    AGENT_SYSTEM_TEMPLATE,
    CONCEPTUAL_SYSTEM_PROMPT,
    ROUTER_SYSTEM_PROMPT,
)
from tools import TOOLS_RESERVAS


class RutaConsulta(BaseModel):
    """Ruta seleccionada para atender la solicitud del estudiante."""

    ruta: Literal["conceptual", "herramientas"] = Field(
        description=(
            "Usa 'conceptual' para saludos y dudas generales sobre el proceso "
            "de reserva que NO requieren datos reales. Usa 'herramientas' para "
            "consultar disponibilidad, reservar, ver reservas propias, fechas "
            "o eventos del campus, y para respuestas cortas dentro de una "
            "reserva en curso."
        )
    )
    motivo: str = Field(
        description="Justificación breve (máx. 15 palabras) de la selección."
    )


@lru_cache(maxsize=None)
def _modelo(temperatura: float) -> ChatGoogleGenerativeAI:
    """Crea el modelo la primera vez que se necesita, no al importar el módulo."""
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        api_key=GEMINI_API_KEY,
        temperature=temperatura,
    )


def _pasos(state: ReservaState, nombre: str) -> list[str]:
    return state.get("pasos_ejecutados", []) + [nombre]


def _reserva_fue_exitosa(mensajes: list) -> bool:
    """Revisa si reservar_espacio devolvió {"exito": True} en estos mensajes."""
    for mensaje in mensajes:
        if getattr(mensaje, "name", None) != "reservar_espacio":
            continue

        datos = mensaje.content
        if isinstance(datos, str):
            texto = datos.strip()
            datos = None
            for parser in (json.loads, ast.literal_eval):
                try:
                    datos = parser(texto)
                    break
                except (ValueError, SyntaxError):
                    continue

        if isinstance(datos, dict) and datos.get("exito") is True:
            return True

    return False


# Nodo 1: Clasificador estructurado
def enrutador_node(state: ReservaState) -> dict:
    ultimo_mensaje = str(state["messages"][-1].content)

    decision = _modelo(0.0).with_structured_output(RutaConsulta).invoke(
        [
            SystemMessage(content=ROUTER_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"Memoria reciente:\n{state.get('memoria') or 'Sin memoria.'}\n\n"
                    f"Mensaje del estudiante:\n{ultimo_mensaje}"
                )
            ),
        ]
    )

    # Si el modelo no devuelve una clasificación válida, el agente es la ruta
    # segura: también sabe responder consultas generales.
    if decision is None:
        ruta = "herramientas"
        motivo = "Clasificación no disponible; se usa el agente por defecto."
    else:
        ruta, motivo = decision.ruta, decision.motivo

    return {
        "ruta": ruta,
        "motivo": motivo,
        "pasos_ejecutados": _pasos(state, "enrutador"),
    }


# Nodo 2: Respuesta general sin herramientas
def conceptual_node(state: ReservaState) -> dict:
    sistema = (
        f"{CONCEPTUAL_SYSTEM_PROMPT}\n\n"
        f"MEMORIA RECIENTE:\n{state.get('memoria') or 'Sin memoria reciente.'}"
    )

    respuesta = _modelo(0.2).invoke(
        [SystemMessage(content=sistema), *state["messages"]]
    )

    return {
        "messages": [respuesta],
        "pasos_ejecutados": _pasos(state, "nodo_conceptual"),
    }


# Nodo 3: Razonamiento con herramientas vinculadas
def agente_reservas_node(state: ReservaState) -> dict:
    estudiante = state["estudiante"]

    sistema = AGENT_SYSTEM_TEMPLATE.format(
        nombre=estudiante.get("nombre", "No registrado"),
        correo=estudiante.get("correo", "No registrado"),
        memoria=state.get("memoria") or "Sin memoria reciente.",
    )

    modelo_con_tools = _modelo(0.1).bind_tools(TOOLS_RESERVAS)
    respuesta = modelo_con_tools.invoke(
        [SystemMessage(content=sistema), *state["messages"]]
    )

    return {
        "messages": [respuesta],
        "pasos_ejecutados": _pasos(state, "agente_reservas"),
    }


# Nodo 4: Ejecución nativa con ToolNode
_ejecutor_tools = ToolNode(TOOLS_RESERVAS, handle_tool_errors=True)


def herramientas_node(state: ReservaState) -> dict:
    resultado = _ejecutor_tools.invoke(state)
    nuevos = resultado["messages"]

    usadas = list(state.get("herramientas_usadas", []))
    for mensaje in nuevos:
        nombre = getattr(mensaje, "name", None)
        if nombre and nombre not in usadas:
            usadas.append(nombre)

    return {
        "messages": nuevos,
        "herramientas_usadas": usadas,
        "reserva_exitosa": state.get("reserva_exitosa", False)
        or _reserva_fue_exitosa(nuevos),
        "pasos_ejecutados": _pasos(state, "herramientas"),
    }