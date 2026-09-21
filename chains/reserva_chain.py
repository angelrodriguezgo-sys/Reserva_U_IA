

"""Chain especializada en extraer la intención de reserva del estudiante.

Esta Chain analiza el mensaje del usuario y devuelve una estructura
Pydantic con los datos necesarios para gestionar una reserva de espacio:
acción, espacio, fecha, horas, motivo y datos faltantes.

Se utiliza ANTES de invocar el Agent, para verificar que tenemos toda
la información y poder pedir al usuario los datos que falten de forma
explícita.
"""

from typing import Optional

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from config.settings import GEMINI_API_KEY, GEMINI_MODEL


# ──────────────────────────────────────────────────────────────────────
# Modelo Pydantic de salida
# ──────────────────────────────────────────────────────────────────────

class IntencionReserva(BaseModel):
    """Datos estructurados extraídos de una solicitud de reserva."""

    accion: str = Field(
        description=(
            "Acción detectada: 'reservar', 'cancelar', 'consultar' o "
            "'modificar'. Usa 'desconocida' si no se puede determinar."
        )
    )
    espacio: Optional[str] = Field(
        default=None,
        description="Nombre o id del espacio mencionado (ej: 'Sala 301', 'lab-2')."
    )
    fecha: Optional[str] = Field(
        default=None,
        description="Fecha en formato YYYY-MM-DD si se menciona explícitamente."
    )
    hora_inicio: Optional[str] = Field(
        default=None,
        description="Hora de inicio en formato HH:MM (ej: '14:00')."
    )
    hora_fin: Optional[str] = Field(
        default=None,
        description="Hora de fin en formato HH:MM (ej: '16:00')."
    )
    motivo: Optional[str] = Field(
        default=None,
        description="Motivo o propósito de la reserva si se menciona."
    )
    datos_faltantes: list[str] = Field(
        default_factory=list,
        description=(
            "Lista de datos indispensables que el usuario aún debe "
            "proporcionar. Ej: ['fecha', 'hora_inicio']."
        )
    )


# ──────────────────────────────────────────────────────────────────────
# System prompt
# ──────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT_RESERVA = """
Eres un asistente experto en reserva de espacios académicos de la
Universidad Católica Luis Amigó.

Tu tarea es analizar el mensaje del estudiante y extraer la información
estructurada necesaria para gestionar una reserva de espacio.

REGLAS:
- Si el estudiante no indica la acción, intenta inferirla del contexto
  y de la memoria reciente.
- Marca en 'datos_faltantes' cualquier dato indispensable que no aparezca.
- Datos indispensables para 'reservar': espacio, fecha, hora_inicio,
  hora_fin.
- Datos indispensables para 'cancelar': espacio, fecha, hora_inicio.
- Datos indispensables para 'consultar': fecha (espacio es opcional).
- Datos indispensables para 'modificar': espacio, fecha, hora_inicio
  y al menos un dato nuevo (nueva fecha, nueva hora, etc.).
- NO inventes datos que el estudiante no haya mencionado.
- Si el estudiante dice algo como "mañana" o "el viernes", no lo
  conviertas a fecha exacta; déjalo en 'fecha' tal cual para que el
  agente lo resuelva con la tool de fecha.
""".strip()


# ──────────────────────────────────────────────────────────────────────
# Fábrica de la Chain
# ──────────────────────────────────────────────────────────────────────

def crear_reserva_chain():
    """Crea la Chain que extrae la intención de reserva estructurada."""
    model = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        api_key=GEMINI_API_KEY,
        temperature=0,
    )

    structured_model = model.with_structured_output(IntencionReserva)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT_RESERVA),
            (
                "human",
                "Mensaje del estudiante:\n{pregunta}\n\n"
                "Memoria reciente:\n{memoria}",
            ),
        ]
    )

    return prompt | structured_model