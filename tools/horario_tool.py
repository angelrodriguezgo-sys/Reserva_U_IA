"""Utilidades para consultar y gestionar la reserva de espacios universitarios."""

import json
from pathlib import Path
from typing import TypedDict, Optional


class Franja(TypedDict):
    dia: str
    hora: str
    disponible: bool
    reservado_por: Optional[str]


class Espacio(TypedDict):
    nombre: str
    capacidad: int
    franjas: list[Franja]


DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "horarios.json"


def _cargar_espacios() -> list[Espacio]:
    with DATA_FILE.open("r", encoding="utf-8") as archivo:
        return json.load(archivo)


def _guardar_espacios(espacios: list[Espacio]) -> None:
    with DATA_FILE.open("w", encoding="utf-8") as archivo:
        json.dump(espacios, archivo, ensure_ascii=False, indent=2)


def consultar_espacios_disponibles(dia: str = "") -> dict:
    """Consulta los espacios con franjas disponibles.

    Args:
        dia: Día de la semana para filtrar (opcional). Si se deja vacío,
            se muestran todas las franjas disponibles de todos los días.

    Returns:
        Diccionario con la lista de espacios y sus franjas libres,
        incluyendo nombre, capacidad, día y hora.
    """
    espacios = _cargar_espacios()
    criterio = dia.lower().strip()

    resultados = []
    for espacio in espacios:
        franjas_libres = [
            f for f in espacio["franjas"]
            if f["disponible"] and (not criterio or criterio in f["dia"].lower())
        ]
        if franjas_libres:
            resultados.append({
                "nombre": espacio["nombre"],
                "capacidad": espacio["capacidad"],
                "franjas_disponibles": franjas_libres,
            })

    return {
        "dia_consultado": dia or "todos",
        "espacios": resultados,
        "cantidad": len(resultados),
    }


def reservar_espacio(
    nombre_espacio: str,
    dia: str,
    hora: str,
    nombre_estudiante: str,
    correo_estudiante: str,
) -> dict:
    """Reserva una franja horaria de un espacio si está disponible.

    Marca la franja como ocupada y registra el estudiante que la reservó.

    Args:
        nombre_espacio: Nombre del espacio a reservar (ej. "Sala 301").
        dia: Día de la semana de la reserva.
        hora: Franja horaria exacta a reservar.
        nombre_estudiante: Nombre del estudiante que reserva.
        correo_estudiante: Correo (usuario) del estudiante que reserva.

    Returns:
        Diccionario con el resultado de la operación: éxito o el motivo
        del fallo (espacio no encontrado, franja no encontrada, o ya ocupada).
    """
    espacios = _cargar_espacios()

    for espacio in espacios:
        if espacio["nombre"].lower() == nombre_espacio.lower():
            for franja in espacio["franjas"]:
                if (
                    franja["dia"].lower() == dia.lower()
                    and franja["hora"] == hora
                ):
                    if not franja["disponible"]:
                        return {
                            "exito": False,
                            "mensaje": f"La franja {dia} {hora} en {nombre_espacio} ya está ocupada.",
                        }

                    franja["disponible"] = False
                    franja["reservado_por"] = f"{nombre_estudiante} ({correo_estudiante})"
                    _guardar_espacios(espacios)

                    return {
                        "exito": True,
                        "mensaje": f"Reserva confirmada: {nombre_espacio}, {dia}, {hora}, a nombre de {nombre_estudiante}.",
                    }

            return {"exito": False, "mensaje": "Franja horaria no encontrada para ese espacio."}

    return {"exito": False, "mensaje": f"No se encontró el espacio '{nombre_espacio}'."}

def consultar_mis_reservas(correo_estudiante: str) -> dict:
    """Busca todas las reservas activas asociadas a un correo de estudiante.

    Recorre todos los espacios y franjas para encontrar aquellas ocupadas
    por el estudiante cuyo correo coincide con el indicado.

    Args:
        correo_estudiante: Correo (usuario) del estudiante que consulta
            sus reservas.

    Returns:
        Diccionario con la lista de reservas encontradas (espacio, día,
        hora) y la cantidad total. Lista vacía si no tiene reservas.
    """
    espacios = _cargar_espacios()
    correo = correo_estudiante.lower().strip()

    reservas = [
        {
            "espacio": espacio["nombre"],
            "dia": franja["dia"],
            "hora": franja["hora"],
        }
        for espacio in espacios
        for franja in espacio["franjas"]
        if not franja["disponible"]
        and franja["reservado_por"]
        and correo in franja["reservado_por"].lower()
    ]

    return {
        "correo_consultado": correo_estudiante,
        "reservas": reservas,
        "cantidad": len(reservas),
    }