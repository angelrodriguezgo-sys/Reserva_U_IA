"""Chain para recomendar el mejor espacio disponible según las necesidades del estudiante."""

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from config.settings import GEMINI_API_KEY, GEMINI_MODEL

SYSTEM_PROMPT_RECOMENDACION = """
Eres un asistente que ayuda a un estudiante a elegir el mejor espacio
disponible entre varias opciones, según lo que necesita.

Recibirás una lista de espacios disponibles (con capacidad y equipamiento)
y el contexto de lo que el estudiante busca. Recomienda 1 o 2 opciones,
explicando brevemente por qué encajan mejor. Sé breve (máximo 3 líneas).
No inventes espacios que no estén en la lista.
""".strip()


def serializar_espacios(espacios: list[dict]) -> str:
    """Convierte la lista de espacios disponibles en texto legible para el prompt."""
    if not espacios:
        return "No hay espacios disponibles."

    return "\n".join(
        f"- {e['nombre']} (capacidad: {e['capacidad']}, equipamiento: {', '.join(e.get('equipamiento', [])) or 'ninguno'})"
        for e in espacios
    )


def crear_recomendacion_chain():
    """Crea la Chain que recomienda un espacio entre las opciones disponibles."""
    model = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        api_key=GEMINI_API_KEY,
        temperature=0.2,
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT_RECOMENDACION),
            (
                "human",
                "Espacios disponibles:\n{espacios}\n\n"
                "Lo que necesita el estudiante:\n{contexto}",
            ),
        ]
    )

    return prompt | model | StrOutputParser()