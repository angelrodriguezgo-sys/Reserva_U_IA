# tools/horario_tool.py


"""Utilidades para consultar y gestionar la reserva de espacios universitarios.

Usa tres archivos de datos:
- espacios.json: información fija de cada espacio.
- horarios.json: catálogo de franjas horarias reservables.
- reservas.json: registros dinámicos de reservas (referencia espacio + horario + fecha).
"""

import json
import uuid
from datetime import date, timedelta
from pathlib import Path
from typing import Optional, TypedDict
from langchain.tools import tool


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
ESPACIOS_FILE = DATA_DIR / "espacios.json"
HORARIOS_FILE = DATA_DIR / "horarios.json"
RESERVAS_FILE = DATA_DIR / "reservas.json"

DIAS_SEMANA = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]



class Espacio(TypedDict):
    id: str
    nombre: str
    capacidad: int
    tipo: str
    equipamiento: list[str]
    mantenimiento_recurrente: list[str]
    mantenimiento_fechas: list[str]


class FranjaHoraria(TypedDict):
    id: str
    hora_inicio: str
    hora_fin: str


class Reserva(TypedDict):
    id: str
    espacio_id: str
    horario_id: str
    fecha: str
    nombre_estudiante: str
    correo_estudiante: str


# ---------- Carga y guardado ----------

def _cargar_espacios() -> list[Espacio]:
    with ESPACIOS_FILE.open("r", encoding="utf-8") as archivo:
        return json.load(archivo)


def _cargar_horarios() -> list[FranjaHoraria]:
    with HORARIOS_FILE.open("r", encoding="utf-8") as archivo:
        return json.load(archivo)


def _cargar_reservas() -> list[Reserva]:
    with RESERVAS_FILE.open("r", encoding="utf-8") as archivo:
        return json.load(archivo)


def _guardar_reservas(reservas: list[Reserva]) -> None:
    with RESERVAS_FILE.open("w", encoding="utf-8") as archivo:
        json.dump(reservas, archivo, ensure_ascii=False, indent=2)


def _buscar_espacio(espacios: list[Espacio], espacio_id_o_nombre: str) -> Optional[Espacio]:
    criterio = espacio_id_o_nombre.lower().strip()
    for espacio in espacios:
        if espacio["id"].lower() == criterio or espacio["nombre"].lower() == criterio:
            return espacio
    return None


def _buscar_horario(horarios: list[FranjaHoraria], hora_texto: str) -> Optional[FranjaHoraria]:
    """Encuentra la franja horaria que coincide con un texto 'HH:MM-HH:MM'."""
    criterio = hora_texto.replace(" ", "")
    for h in horarios:
        if f"{h['hora_inicio']}-{h['hora_fin']}" == criterio:
            return h
    return None


def _espacio_cerrado(espacio: Espacio, fecha: date) -> bool:
    nombre_dia = DIAS_SEMANA[fecha.weekday()]
    return (
        nombre_dia in espacio.get("mantenimiento_recurrente", [])
        or fecha.isoformat() in espacio.get("mantenimiento_fechas", [])
    )


# ---------- Herramientas expuestas al agente ----------

@tool
def consultar_horarios_disponibles_dia() -> dict:
    """Devuelve el catálogo completo de franjas horarias reservables (fijo para todos los espacios)."""
    horarios = _cargar_horarios()
    return {
        "franjas": [f"{h['hora_inicio']}-{h['hora_fin']}" for h in horarios],
    }

@tool
def consultar_espacios_disponibles(fecha: str, hora: str = "") -> dict:
    """Consulta espacios disponibles en una fecha (y franja horaria opcional).

    Args:
        fecha: Fecha a consultar, en formato YYYY-MM-DD.
        hora: Franja horaria exacta del catálogo, ej. "08:00-10:00".

    Returns:
        Diccionario con los espacios disponibles ese día/hora, incluyendo
        capacidad y equipamiento.
    """
    try:
        fecha_obj = date.fromisoformat(fecha)
    except ValueError:
        return {"error": "Formato de fecha inválido. Usa YYYY-MM-DD."}

    espacios = _cargar_espacios()
    horarios = _cargar_horarios()
    reservas = _cargar_reservas()

    horario_filtro = _buscar_horario(horarios, hora) if hora else None
    if hora and not horario_filtro:
        return {"error": f"La franja '{hora}' no existe en el catálogo de horarios."}

    disponibles = []
    for espacio in espacios:
        if _espacio_cerrado(espacio, fecha_obj):
            continue

        ocupado = any(
            r["espacio_id"] == espacio["id"]
            and r["fecha"] == fecha
            and (not horario_filtro or r["horario_id"] == horario_filtro["id"])
            for r in reservas
        )
        if ocupado:
            continue

        disponibles.append({
            "id": espacio["id"],
            "nombre": espacio["nombre"],
            "capacidad": espacio["capacidad"],
            "equipamiento": espacio.get("equipamiento", []),
        })

    return {
        "fecha_consultada": fecha,
        "hora_consultada": hora or "todas las franjas",
        "espacios_disponibles": disponibles,
        "cantidad": len(disponibles),
    }

@tool
def reservar_espacio(
    espacio_id_o_nombre: str,
    fecha: str,
    hora: str,
    nombre_estudiante: str,
    correo_estudiante: str,
) -> dict:
    """Reserva un espacio en una fecha y franja horaria del catálogo."""
    try:
        fecha_obj = date.fromisoformat(fecha)
    except ValueError:
        return {"exito": False, "mensaje": "Formato de fecha inválido. Usa YYYY-MM-DD."}

    if fecha_obj < date.today():
        return {"exito": False, "mensaje": "No se puede reservar en una fecha pasada."}

    espacios = _cargar_espacios()
    espacio = _buscar_espacio(espacios, espacio_id_o_nombre)
    if not espacio:
        return {"exito": False, "mensaje": f"No se encontró el espacio '{espacio_id_o_nombre}'."}

    if _espacio_cerrado(espacio, fecha_obj):
        return {"exito": False, "mensaje": f"{espacio['nombre']} está cerrado por mantenimiento ese día."}

    horarios = _cargar_horarios()
    horario = _buscar_horario(horarios, hora)
    if not horario:
        return {"exito": False, "mensaje": f"La franja '{hora}' no existe en el catálogo de horarios."}

    reservas = _cargar_reservas()
    ya_ocupado = any(
        r["espacio_id"] == espacio["id"] and r["fecha"] == fecha and r["horario_id"] == horario["id"]
        for r in reservas
    )
    if ya_ocupado:
        return {"exito": False, "mensaje": f"La franja {hora} el {fecha} en {espacio['nombre']} ya está reservada."}

    nueva_reserva: Reserva = {
        "id": str(uuid.uuid4()),
        "espacio_id": espacio["id"],
        "horario_id": horario["id"],
        "fecha": fecha,
        "nombre_estudiante": nombre_estudiante,
        "correo_estudiante": correo_estudiante,
    }
    reservas.append(nueva_reserva)
    _guardar_reservas(reservas)

    return {
        "exito": True,
        "mensaje": f"Reserva confirmada: {espacio['nombre']}, {fecha}, {hora}, a nombre de {nombre_estudiante}.",
    }

@tool
def consultar_mis_reservas(correo_estudiante: str) -> dict:
    """Busca las reservas activas asociadas a un correo de estudiante."""
    espacios = {e["id"]: e["nombre"] for e in _cargar_espacios()}
    horarios = {h["id"]: f"{h['hora_inicio']}-{h['hora_fin']}" for h in _cargar_horarios()}
    reservas = _cargar_reservas()
    correo = correo_estudiante.lower().strip()

    mias = [
        {
            "espacio": espacios.get(r["espacio_id"], r["espacio_id"]),
            "fecha": r["fecha"],
            "hora": horarios.get(r["horario_id"], r["horario_id"]),
        }
        for r in reservas
        if r["correo_estudiante"].lower() == correo
    ]

    return {
        "correo_consultado": correo_estudiante,
        "reservas": mias,
        "cantidad": len(mias),
    }

@tool
def generar_calendario_mes(espacio_id_o_nombre: str, anio: int, mes: int) -> dict:
    """Genera la disponibilidad día por día de un espacio para un mes completo."""
    espacios = _cargar_espacios()
    espacio = _buscar_espacio(espacios, espacio_id_o_nombre)
    if not espacio:
        return {"error": f"No se encontró el espacio '{espacio_id_o_nombre}'."}

    horarios = {h["id"]: f"{h['hora_inicio']}-{h['hora_fin']}" for h in _cargar_horarios()}
    reservas = _cargar_reservas()

    primer_dia = date(anio, mes, 1)
    siguiente_mes = date(anio + (mes == 12), (mes % 12) + 1, 1)
    dias_en_mes = (siguiente_mes - primer_dia).days

    calendario = []
    for i in range(dias_en_mes):
        fecha_actual = primer_dia + timedelta(days=i)
        fecha_str = fecha_actual.isoformat()

        cerrado = _espacio_cerrado(espacio, fecha_actual)
        reservas_del_dia = [
            {"hora": horarios.get(r["horario_id"], r["horario_id"]), "reservado_por": r["nombre_estudiante"]}
            for r in reservas
            if r["espacio_id"] == espacio["id"] and r["fecha"] == fecha_str
        ]

        calendario.append({
            "fecha": fecha_str,
            "dia_semana": DIAS_SEMANA[fecha_actual.weekday()],
            "estado": "cerrado" if cerrado else "disponible",
            "reservas": reservas_del_dia,
        })

    return {"espacio": espacio["nombre"], "anio": anio, "mes": mes, "calendario": calendario}