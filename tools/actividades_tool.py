# actividades_tool.py
"""Tools para consultar y priorizar actividades académicas."""



import json


from pathlib import Path



from langchain.tools import tool



from chains.reserva_chain import (


    crear_priorizacion_chain,


    serializar_actividades,


)



DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "actividades.json"




def _cargar_actividades() -> list[dict]:


    with DATA_FILE.open("r", encoding="utf-8") as archivo:


        return json.load(archivo)




@tool


def consultar_actividades(consulta: str = "pendientes") -> dict:


    """Consulta actividades académicas por estado, asignatura o palabra clave."""


    actividades = _cargar_actividades()


    criterio = consulta.lower().strip()



    if criterio in {"todas", "todo", "*"}:


        resultados = actividades


    elif criterio in {"pendientes", "pendiente"}:


        resultados = [


            a for a in actividades


            if a["estado"].lower() == "pendiente"


        ]


    else:


        resultados = [


            a for a in actividades


            if criterio in a["estado"].lower()


            or criterio in a["asignatura"].lower()


            or criterio in a["actividad"].lower()


        ]



    return {


        "consulta": consulta,


        "resultados": resultados,


        "cantidad": len(resultados),


    }




@tool


def priorizar_actividades(contexto: str = "") -> str:


    """Prioriza las actividades pendientes mediante una Chain determinista."""


    actividades = [


        a for a in _cargar_actividades()


        if a["estado"].lower() == "pendiente"


    ]



    chain = crear_priorizacion_chain()



    return chain.invoke(


        {


            "actividades": serializar_actividades(actividades),


            "contexto": contexto or "Sin contexto adicional.",


        }


    )