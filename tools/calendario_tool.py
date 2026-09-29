

#calendario_tool.py
"""Tool para consultar eventos del calendario académico ficticio."""



import json


from pathlib import Path



from langchain.tools import tool



DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "calendario.json"




@tool


def consultar_calendario_academico(consulta: str) -> dict:


    """Consulta fechas o eventos del calendario académico por palabra clave."""


    with DATA_FILE.open("r", encoding="utf-8") as archivo:


        eventos = json.load(archivo)



    criterio = consulta.lower().strip()



    resultados = [


        evento


        for evento in eventos


        if criterio in evento["evento"].lower()


        or criterio in evento["descripcion"].lower()


        or criterio in evento["fecha"].lower()


    ]



    return {


        "consulta": consulta,


        "resultados": resultados,


        "cantidad": len(resultados),


    }