"""Tool que recomienda el mejor espacio disponible según las necesidades del estudiante."""

from langchain.tools import tool
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from config.settings import GEMINI_API_KEY, GEMINI_MODEL
from tools.horario_tool import consultar_espacios_disponibles

SYSTEM_PROMPT_RECOMENDACION = """
Eres un asistente que ayuda a un estudiante a elegir el mejor espacio
disponible entre varias opciones, según lo que necesita.

Recibirás una lista de espacios disponibles (con capacidad y equipamiento)
y el contexto de lo que el estudiante busca. Recomienda 1 o 2 opciones,
explicando brevemente por qué encajan mejor. Sé breve (máximo 3 líneas).
No inventes espacios que no estén en la lista.
""".strip()


def _serializar_espacios(espacios: list[dict]) -> str:
    """Convierte los espacios disponibles en texto legible para el prompt."""
    return "\n".join(
        f"- {e['nombre']} (capacidad: {e['capacidad']}, "
        f"equipamiento: {', '.join(e.get('equipamiento', [])) or 'ninguno'})"
        for e in espacios
    )


def _crear_recomendacion_chain():
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


@tool
def recomendar_espacio(fecha: str, hora: str = "", contexto: str = "") -> str:
    """Recomienda el mejor espacio disponible según lo que necesita el estudiante.

    Args:
        fecha: Fecha a consultar, en formato YYYY-MM-DD.
        hora: Franja horaria exacta del catálogo, ej. "08:00-10:00". Opcional.
        contexto: Lo que necesita el estudiante (ej. "grupo de 10 personas,
            necesita proyector").
    """
    resultado = consultar_espacios_disponibles.invoke({"fecha": fecha, "hora": hora})

    if "error" in resultado:
        return resultado["error"]

    if not resultado["espacios_disponibles"]:
        return "No hay espacios disponibles para esa fecha y franja."

    chain = _crear_recomendacion_chain()
    return chain.invoke(
        {
            "espacios": _serializar_espacios(resultado["espacios_disponibles"]),
            "contexto": contexto or "Sin preferencias específicas.",
        }
    )