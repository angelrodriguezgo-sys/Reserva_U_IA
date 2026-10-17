"""Estado compartido del grafo del Asistente de Reserva de Espacios."""

from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class EstudianteInfo(TypedDict):
    nombre: str
    correo: str


class ReservaState(TypedDict):
    # Reducer automático: gestiona HumanMessage, AIMessage y ToolMessage
    messages: Annotated[list[BaseMessage], add_messages]

    estudiante: EstudianteInfo
    memoria: str                  # Memoria reciente, para AGENT_SYSTEM_TEMPLATE
    ruta: str                     # "conceptual" o "herramientas"
    motivo: str
    herramientas_usadas: list[str]
    pasos_ejecutados: list[str]   # Traza de nodos recorridos
    reserva_exitosa: bool         # True si reservar_espacio devolvió éxito