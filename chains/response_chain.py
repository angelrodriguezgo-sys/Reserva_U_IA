

"""Chain determinista para respuestas académicas generales.

Se utiliza cuando el router determina que la consulta NO requiere
herramientas externas. Ejemplos: saludos, dudas sobre el sistema de
reservas, información general de la universidad, etc.
"""

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from config.settings import GEMINI_API_KEY, GEMINI_MODEL
from prompts.academic_prompt import GENERAL_SYSTEM_PROMPT


def crear_respuesta_chain():
    """Crea la Chain Prompt -> Model -> Parser para respuestas generales."""
    model = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        api_key=GEMINI_API_KEY,
        temperature=0.2,
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", GENERAL_SYSTEM_PROMPT),
            ("human", "{pregunta}"),
        ]
    )

    return prompt | model | StrOutputParser()