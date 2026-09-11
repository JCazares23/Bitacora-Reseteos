# Reporte de reseteos de ADManager

## Intencion del repositorio

Este proyecto convierte los logs diarios del bot de soporte en un reporte CSV de los intentos de reseteo de contrasena realizados mediante ADManager.

Procesa las acciones `users_admin/resetuser` y `users_admin/alta_sap`. El codigo esta separado por modulos para poder agregar nuevas acciones sin rehacer el proceso completo.

El reporte se puede ejecutar mas de una vez para una misma fecha. Si el archivo de entrada no cambia, el CSV final tampoco cambia. Si un log historico se corrige, al ejecutarlo de nuevo solo se agregan registros que aun no existian en el reporte.

## Estructura del proyecto

```text
src/
  reporte_bot/
    __main__.py       # Punto de entrada de la linea de comandos
    pipeline.py       # Coordina la lectura, reglas y escritura
    lector_logs.py    # Lee el log y agrupa eventos por operacion
    admanager.py      # Extrae datos utiles de las respuestas de ADManager
    resetuser.py      # Convierte una operacion resetuser en una fila del reporte
    alta_sap.py       # Convierte una operacion alta_sap en una fila del reporte
    reporte_csv.py    # Valida, combina y guarda el CSV sin duplicados
    texto.py          # Normaliza texto antes de compararlo
tests/                # Pruebas unitarias y de integracion
notebooks/            # Exploracion manual de ejemplos de logs
data/input/           # Logs diarios de entrada, no se suben al repositorio
data/output/          # Reporte generado, no se sube al repositorio
```

El notebook es solo material de exploracion. El proceso real se ejecuta desde la linea de comandos.

## Instalacion

Se necesita tener [uv](https://docs.astral.sh/uv/) instalado. Desde la raiz del repositorio ejecuta:

```powershell
uv sync
```

El comando crea el entorno virtual e instala las dependencias del proyecto.

## Preparar un log

Guarda el log que deseas procesar dentro de `data/input/` con este formato de nombre:

```text
AAAA-MM-DD.log
```

Por ejemplo, para procesar el 1 de septiembre de 2026, el archivo debe llamarse `data/input/2026-09-01.log`.

## Ejecutar el reporte

Desde la raiz del proyecto, en cualquier sistema operativo:

```bash
uv run reporte-bot --fecha 2026-09-01
```

`uv sync` instala este comando al preparar el proyecto. En Windows tambien se
puede ejecutar directamente como `\.venv\Scripts\reporte-bot.exe --fecha
2026-09-01`.

El resultado se guarda en `data/output/tabla_reporte_bot.csv`. La fecha es obligatoria para que quede claro que log se esta procesando.

## Especificacion del reporte

El CSV final contiene estas columnas:

```text
timestamp
solicitante
target
accion
sistema
nombre completo del usuario solicitante
nombre completo del usuario target
oficina del usuario solicitante
oficina del usuario target
resultado
```

La columna `resultado` usa mensajes entendibles para una persona. El proyecto interpreta los codigos de respuesta del bot y los datos encontrados en ADManager para explicar si un reseteo o alta SAP fue exitoso, si faltaba algun usuario, si no habia permisos o si ocurrio otro problema.

## Por que no se duplican filas

Antes de escribir el reporte, el programa compara cada fila nueva con las que ya existen en el CSV. Una fila identica se conserva una sola vez. Esto permite repetir una ejecucion sin alterar el resultado y recuperar informacion nueva al reprocesar un log corregido.

## Pruebas y revision de codigo

Las pruebas usan datos de ejemplo, nunca los logs reales. Para ejecutarlas en Windows PowerShell:

```powershell
.\.venv\Scripts\ruff.exe check src tests
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

En Linux o macOS:

```bash
uv run ruff check src tests
PYTHONPATH=src uv run python -m unittest discover -s tests -v
```

Las pruebas cubren la normalizacion de texto, la lectura de logs, la informacion de ADManager, las reglas de `resetuser`, la escritura idempotente del CSV y la ejecucion completa desde la linea de comandos.
