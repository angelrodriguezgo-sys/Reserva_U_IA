"""Grafo del Asistente de Reserva de Espacios con LangGraph.

Flujo:
    START -> enrutador -> nodo_conceptual -> END
                       -> agente_reservas <-> herramientas (bucle) -> END
"""

from functools import lru_cache

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from graph.nodes import (
    agente_reservas_node,
    conceptual_node,
    enrutador_node,
    herramientas_node,
)
from graph.state import EstudianteInfo, ReservaState

MENSAJE_VACIO = "No fue posible generar una respuesta."


def _decidir_ruta(state: ReservaState) -> str:
    """Bifurcación del enrutador: respuesta general o agente con herramientas."""
    if state.get("ruta") == "conceptual":
        return "nodo_conceptual"
    return "agente_reservas"


def _evaluar_tools(state: ReservaState) -> str:
    """¿El agente pidió herramientas o ya tiene la respuesta final?"""
    ultimo = state["messages"][-1]
    if getattr(ultimo, "tool_calls", None):
        return "herramientas"
    return END


def crear_grafo_reservas():
    builder = StateGraph(ReservaState)

    builder.add_node("enrutador", enrutador_node)
    builder.add_node("nodo_conceptual", conceptual_node)
    builder.add_node("agente_reservas", agente_reservas_node)
    builder.add_node("herramientas", herramientas_node)

    # Arista inicial
    builder.add_edge(START, "enrutador")

    # Bifurcación del enrutador
    builder.add_conditional_edges(
        "enrutador",
        _decidir_ruta,
        {
            "nodo_conceptual": "nodo_conceptual",
            "agente_reservas": "agente_reservas",
        },
    )

    # Arista condicional: ¿llamar a herramientas o terminar?
    builder.add_conditional_edges(
        "agente_reservas",
        _evaluar_tools,
        {"herramientas": "herramientas", END: END},
    )

    # Bucle cíclico: de herramientas retorna al agente
    builder.add_edge("herramientas", "agente_reservas")

    builder.add_edge("nodo_conceptual", END)

    return builder.compile(checkpointer=MemorySaver())


@lru_cache(maxsize=1)
def obtener_grafo():
    """Compila el grafo una sola vez, para que MemorySaver conserve las conversaciones."""
    return crear_grafo_reservas()


def _extraer_texto_final(mensajes: list) -> str:
    """Extrae el texto del último mensaje, que puede ser str o lista de bloques."""
    if not mensajes:
        return MENSAJE_VACIO

    contenido = mensajes[-1].content

    if isinstance(contenido, str):
        return contenido.strip() or MENSAJE_VACIO

    if isinstance(contenido, list):
        partes = []
        for bloque in contenido:
            if isinstance(bloque, dict) and bloque.get("type") == "text":
                partes.append(str(bloque.get("text", "")))
            elif isinstance(bloque, str):
                partes.append(bloque)
        return "\n".join(p for p in partes if p).strip() or MENSAJE_VACIO

    return str(contenido)


def responder(
    mensaje_usuario: str,
    estudiante: EstudianteInfo,
    memoria: str,
    thread_id: str,
) -> dict:
    """Ejecuta el grafo y devuelve el resultado que usa la interfaz."""
    estado_inicial = {
        "messages": [("user", mensaje_usuario)],
        "estudiante": dict(estudiante),
        "memoria": memoria,
        # Se reinician en cada turno; sin esto, reserva_exitosa seguiría en True.
        "ruta": "",
        "motivo": "",
        "herramientas_usadas": [],
        "pasos_ejecutados": [],
        "reserva_exitosa": False,
    }

    resultado = obtener_grafo().invoke(
        estado_inicial,
        config={"configurable": {"thread_id": thread_id}},
    )

    return {
        "respuesta": _extraer_texto_final(resultado.get("messages", [])),
        "ruta": resultado.get("ruta", ""),
        "motivo": resultado.get("motivo", ""),
        "tools": resultado.get("herramientas_usadas", []),
        "reserva_exitosa": resultado.get("reserva_exitosa", False),
        "pasos": resultado.get("pasos_ejecutados", []),
    }