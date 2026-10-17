from tools.eventos_campus_tool import consultar_eventos_campus
from tools.fecha_tool import obtener_fecha, resolver_fecha_relativa
from tools.horario_tool import (
    consultar_espacios_disponibles,
    consultar_horarios_disponibles_dia,
    consultar_mis_reservas,
    generar_calendario_mes,
    reservar_espacio,
)
from tools.recomendacion_tool import recomendar_espacio

TOOLS_RESERVAS = [
    obtener_fecha,
    resolver_fecha_relativa,
    consultar_horarios_disponibles_dia,
    consultar_espacios_disponibles,
    recomendar_espacio,
    generar_calendario_mes,
    consultar_eventos_campus,
    consultar_mis_reservas,
    reservar_espacio,
]