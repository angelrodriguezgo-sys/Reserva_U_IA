


"""Chain de clasificación para decidir entre Chain y Agent.

Este router analiza el mensaje del estudiante y decide si la consulta
puede resolverse con una Chain simple (respuesta directa) o si requiere
un Agent con herramientas externas (gestión de espacios y reservas).
"""

from typing import Literal

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from config.settings import GEMINI_API_KEY, GEMINI_MODEL
from prompts.academic_prompt import ROUTER_SYSTEM_PROMPT


class RutaConsulta(BaseModel):
    """Ruta seleccionada para atender la solicitud del estudiante."""

    ruta: Literal["chain", "agent"] = Field(
        description=(
            "Usa 'chain' para saludos, preguntas generales, información "
            "sobre el sistema de reservas o consultas académicas que NO "
            "requieren datos externos. "
            "Usa 'agent' cuando el estudiante quiera consultar espacios "
            "disponibles, hacer una reserva, cancelarla, ver sus reservas "
            "o consultar horarios. En resumen: cualquier acción que "
            "requiera ejecutar herramientas."
        )
    )
    motivo: str = Field(
        description="Justificación breve (máx. 15 palabras) de la selección."
    )


def crear_router_chain():
    """Crea la Chain que clasifica la intención del estudiante."""
    model = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        api_key=GEMINI_API_KEY,
        temperature=0,
    )

    structured_model = model.with_structured_output(RutaConsulta)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", ROUTER_SYSTEM_PROMPT),
            ("human", "{pregunta}"),
        ]
    )

    return prompt | structured_model