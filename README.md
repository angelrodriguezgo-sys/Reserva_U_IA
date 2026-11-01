# Prueba de LUXXON – Versión 4.0 (mejora de diseño)

**Objetivo:** probar la nueva versión de LUXXON, la IA de reserva de espacios universitarios, y medir sus tiempos de respuesta, la coherencia con las peticiones y la correcta ejecución.

## Resultados

1. **Inicio y bienvenida.** Se inicia la IA y se envía un saludo básico. LUXXON responde con la bienvenida, una breve explicación de lo que hace y los datos que necesita para funcionar.

2. **Registro de datos.** Se ingresan el nombre y el correo institucional. Tras unos 2,3 segundos, con una breve animación de carga, los datos quedan registrados y se muestran correctamente.

3. **Consulta sin reservas previas.** Se pregunta por una reserva que no existe. LUXXON informa que no hay ninguna registrada y explica qué datos necesita para crearla.

4. **Datos incompletos y duplicados.** Si faltan datos, LUXXON los vuelve a pedir hasta tenerlos todos; sin ellos no crea la reserva. Tampoco permite reservar la misma sala en el mismo horario dos veces, ni por la misma persona ni por otra.

5. **Solicitudes específicas.** Si el estudiante pide requisitos concretos (por ejemplo, equipamiento o cantidad de personas), LUXXON los tiene en cuenta y filtra las salas que mejor los cumplen.

6. **Uso de herramientas.** Al hacer una solicitud específica, la ruta "herramientas" y las herramientas utilizadas se registran en el panel lateral mientras se genera la búsqueda. Luego se muestran las salas disponibles y el proceso continúa.

7. **Errores de escritura.** Aunque el mensaje tenga errores (por ejemplo, "quero la lasa 301"), LUXXON interpreta la petición, corrige el texto y genera la solicitud.

8. **Confirmación.** Antes de reservar, LUXXON muestra un resumen con la sala, la fecha, la hora y los datos del estudiante (nombre y correo), y pide confirmar como medida de precaución. Se puede registrar o cancelar la reserva; si se cancela, LUXXON vuelve a pedir la fecha y la sala.

9. **Reserva exitosa.** Al confirmar, aparece una breve animación de globos y un mensaje de éxito, y el registro de herramientas se actualiza.

10. **Nueva conversación.** Para iniciar una conversación nueva, se deben indicar los datos del nuevo usuario.

11. **Nueva función.** Se agregó el botón "Iniciar con otra cuenta", que permite reservar con otra cuenta sin perder la conversación ni los datos de la cuenta anterior (mejora en base a que solo podia trabajar 1 cuenta a la vez )

12. **Verificacion de pertenencia** Se agrego una verificacion al correo para que solo lo puedan usar las personas de la univeridad luis amigo 

13. **Errores** se evidenciaron retardos en las respuestas por parte del sistema debido a saturacion de uso en su momento y fallas de conexxion de red wifi y de cuota de tokens (ERROR 429).

# Instalación de LUXXON (paso a paso)

## Requisitos
- Computador con conexión a internet (los comandos son para Windows con PowerShell).
- Python 3.10 o superior.
- Git.
- Una clave de API de Gemini (gratuita en Google AI Studio).

## 1. Instalar Python y Git
- Python: https://www.python.org/downloads/ (en el instalador, marca **Add Python to PATH**).
- Git: https://git-scm.com/downloads

Comprueba que quedaron instalados:

```powershell
python --version
git --version
```

## 2. Descargar el proyecto desde GitHub

```powershell
git clone https://github.com/TU_USUARIO/TU_REPOSITORIO.git
cd TU_REPOSITORIO
```

> Sin Git: en la página del repositorio pulsa **Code → Download ZIP**, descomprime la carpeta y ábrela en PowerShell.

## 3. Crear y activar el entorno virtual

```powershell
python -m venv ia
ia\Scripts\Activate.ps1
```

Verás `(ia)` al inicio de la línea. Si aparece un error de "ejecución de scripts deshabilitada", ejecuta esto y vuelve a activar:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

> Mac o Linux: `python3 -m venv ia` y `source ia/bin/activate`.

## 4. Instalar las dependencias

```powershell
pip install -r requirements.txt
```

## 5. Obtener la clave de Gemini
1. Entra a https://aistudio.google.com/apikey con tu cuenta de Google.
2. Crea una clave de API y cópiala.

## 6. Crear el archivo `.env`
En la carpeta principal del proyecto (junto a `app.py`) crea un archivo llamado `.env`. El repositorio no lo trae porque contiene tu clave secreta.

```powershell
New-Item .env
```

Ábrelo con el Bloc de notas o VS Code y escribe:

```
GEMINI_API_KEY=pega_aqui_tu_clave
GEMINI_MODEL=gemini-3.6-flash
```

> No compartas este archivo ni lo subas a GitHub.

## 7. Ejecutar LUXXON

```powershell
streamlit run app.py
```

Se abrirá el navegador en http://localhost:8501. Si Streamlit pide un correo en la terminal, presiona Enter para omitirlo. Para detener la aplicación, presiona `Ctrl + C`.

> Ejecútalo siempre desde la carpeta principal del proyecto, para que encuentre la carpeta `data/` y el tema de colores.

## 8. Probar que funciona
1. Saluda a LUXXON.
2. Escribe tu nombre y tu correo institucional.
3. Pide los espacios disponibles para mañana.
4. Elige una sala, confirma la reserva y comprueba el mensaje de éxito.

Las reservas se guardan en `data/reservas.json` de ese computador.

## Usar LUXXON otro día

```powershell
cd TU_REPOSITORIO
ia\Scripts\Activate.ps1
streamlit run app.py
```

## Actualizar a una versión nueva

```powershell
git pull
pip install -r requirements.txt
```

## Problemas comunes

| Mensaje | Causa | Solución |
|---|---|---|
| `streamlit` no se reconoce o `ModuleNotFoundError` | Entorno sin activar o dependencias sin instalar | Activa `ia` y ejecuta `pip install -r requirements.txt` |
| Error de configuración o de clave | Falta el `.env` o la clave | Revisa el paso 6 |
| `404 NOT_FOUND` del modelo | Google retiró ese modelo | Cambia `GEMINI_MODEL` por un modelo vigente |
| `503 UNAVAILABLE` | Alta demanda temporal en Google | Reintenta en unos minutos |