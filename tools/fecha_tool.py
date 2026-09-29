"""Tool para obtener fecha y día actual, y resolver fechas relativas."""

from datetime import datetime, timedelta

from langchain.tools import tool

DIAS_SEMANA = {
    0: "lunes",
    1: "martes",
    2: "miércoles",
    3: "jueves",
    4: "viernes",
    5: "sábado",
    6: "domingo",
}


@tool
def obtener_fecha() -> dict:
    """Obtiene la fecha actual, el día de la semana y la hora, en español."""
    ahora = datetime.now()
    return {
        "fecha": ahora.strftime("%Y-%m-%d"),
        "dia": DIAS_SEMANA[ahora.weekday()],
        "hora": ahora.strftime("%H:%M"),
    }


@tool
def resolver_fecha_relativa(expresion: str) -> dict:
    """Convierte una expresión relativa de fecha (ej. 'mañana', 'el viernes',
    'hoy', 'pasado mañana') a una fecha exacta en formato YYYY-MM-DD.

    Args:
        expresion: Texto con la expresión relativa a resolver.

    Returns:
        Diccionario con la fecha resuelta, o un mensaje si no se reconoce
        la expresión (en ese caso, pide al estudiante la fecha exacta).
    """
    hoy = datetime.now().date()
    texto = expresion.lower().strip()

    if texto in {"hoy"}:
        resultado = hoy
    elif texto in {"mañana"}:
        resultado = hoy + timedelta(days=1)
    elif texto in {"pasado mañana"}:
        resultado = hoy + timedelta(days=2)
    else:
        nombre_a_indice = {nombre: indice for indice, nombre in DIAS_SEMANA.items()}
        dia_mencionado = next((d for d in nombre_a_indice if d in texto), None)

        if dia_mencionado is None:
            return {
                "resuelta": False,
                "mensaje": f"No pude interpretar la fecha '{expresion}'. Pide al estudiante la fecha exacta (YYYY-MM-DD) o el nombre del día.",
            }

        dias_faltantes = (nombre_a_indice[dia_mencionado] - hoy.weekday()) % 7
        dias_faltantes = dias_faltantes or 7  # si es hoy mismo, asume la próxima semana
        resultado = hoy + timedelta(days=dias_faltantes)

    return {
        "resuelta": True,
        "expresion_original": expresion,
        "fecha": resultado.isoformat(),
        "dia": DIAS_SEMANA[resultado.weekday()],
    }