"""Tool para consultar eventos institucionales que pueden afectar la disponibilidad de espacios."""

import json
from pathlib import Path

from langchain.tools import tool

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "eventos_campus.json"


@tool
def consultar_eventos_campus(consulta: str = "") -> dict:
    """Consulta eventos institucionales (ej. semana de exámenes, graduación)
    que puedan afectar la disponibilidad de espacios en cierta fecha o periodo.

    Args:
        consulta: Palabra clave, nombre del evento o fecha (YYYY-MM-DD) a buscar.
            Si se deja vacío, devuelve todos los eventos registrados.

    Returns:
        Diccionario con los eventos que coinciden con la búsqueda.
    """
    with DATA_FILE.open("r", encoding="utf-8") as archivo:
        eventos = json.load(archivo)

    criterio = consulta.lower().strip()

    if not criterio:
        resultados = eventos
    else:
        resultados = [
            evento for evento in eventos
            if criterio in evento["evento"].lower()
            or criterio in evento["descripcion"].lower()
            or evento["fecha_inicio"] <= criterio <= evento["fecha_fin"]
        ]

    return {
        "consulta": consulta or "todos",
        "resultados": resultados,
        "cantidad": len(resultados),
    }