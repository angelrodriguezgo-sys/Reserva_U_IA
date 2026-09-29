"""Tool que recomienda el mejor espacio disponible según las necesidades del estudiante."""

from langchain.tools import tool

from chains.recomendacion_chain import crear_recomendacion_chain, serializar_espacios
from tools.horario_tool import consultar_espacios_disponibles


@tool
def recomendar_espacio(fecha: str, hora: str = "", contexto: str = "") -> str:
    """Recomienda el mejor espacio disponible para el estudiante en una fecha
    (y franja horaria opcional), según lo que necesita.

    Args:
        fecha: Fecha a consultar, en formato YYYY-MM-DD.
        hora: Franja horaria exacta, ej. "08:00-10:00". Opcional.
        contexto: Lo que el estudiante necesita (ej. "grupo de 10 personas,
            necesita proyector").

    Returns:
        Recomendación en texto explicando qué espacio(s) elegir y por qué.
    """
    resultado = consultar_espacios_disponibles.invoke({"fecha": fecha, "hora": hora})

    if "error" in resultado:
        return resultado["error"]

    chain = crear_recomendacion_chain()
    return chain.invoke(
        {
            "espacios": serializar_espacios(resultado["espacios_disponibles"]),
            "contexto": contexto or "Sin preferencias específicas.",
        }
    )