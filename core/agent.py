"""Integración del asistente de reserva de espacios con la API de Gemini."""

from typing import TypedDict

from google import genai
from google.genai import types

from config.settings import GEMINI_API_KEY, GEMINI_MODEL
from tools.horario_tool import consultar_espacios_disponibles, reservar_espacio

from tools.horario_tool import (
    consultar_espacios_disponibles,
    reservar_espacio,
    consultar_mis_reservas,
)

class Estudiante(TypedDict):
    nombre: str
    correo: str


client = genai.Client(api_key=GEMINI_API_KEY)


def construir_contexto(estudiante: Estudiante, memoria: str) -> str:
    return f"""
Eres un asistente virtual de reserva de espacios universitarios.

Tu objetivo es ayudar al estudiante a reservar salas, laboratorios o aulas.

FLUJO OBLIGATORIO:
1. Si el nombre o el correo del estudiante aún no están registrados,
   pídeselos antes de continuar.
2. Cuando el estudiante quiera reservar un espacio, pregunta el día que necesita.
3. Usa la herramienta consultar_espacios_disponibles para mostrarle los
   espacios libres ese día, indicando nombre, capacidad y horas disponibles.
4. Pide al estudiante que elija un espacio, un día y una hora específica.
5. Antes de reservar, confirma con el estudiante los datos de la reserva
   (espacio, día, hora, nombre y correo).
6. Solo después de la confirmación explícita del estudiante, usa la
   herramienta reservar_espacio para completar la reserva.
7. Informa el resultado (éxito o si la franja ya fue tomada por otro estudiante).
8. Si el estudiante pregunta por sus reservas actuales (ej. "cuáles son mis
   reservas", "qué tengo reservado"), usa la herramienta consultar_mis_reservas
   con su correo registrado y muéstrale la lista (espacio, día y hora).


ESTADO ACTUAL DEL ESTUDIANTE:
Nombre: {estudiante["nombre"]}
Correo: {estudiante["correo"]}

MEMORIA RECIENTE:
{memoria}

No inventes espacios ni disponibilidad: usa siempre las herramientas.
Sé breve, claro y cordial.
""".strip()


def responder(mensaje_usuario: str, estudiante: Estudiante, memoria: str) -> str:
    contexto = construir_contexto(estudiante, memoria)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=mensaje_usuario,
        config=types.GenerateContentConfig(
            system_instruction=contexto,
            tools=[consultar_espacios_disponibles, reservar_espacio, consultar_mis_reservas],
        ),
    )

    return response.text or "No fue posible generar una respuesta."
