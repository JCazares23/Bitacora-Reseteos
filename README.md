# Bitácora de Reseteos

Proyecto para transformar los logs diarios del bot de reseteo de usuarios en un
reporte CSV claro, histórico e idempotente.

## Objetivo

Para una fecha dada, el programa leerá el archivo de log correspondiente,
identificará los reseteos de usuarios gestionados por ADManager y actualizará
`data/output/tabla_reporte_bot.csv` sin duplicar registros.

## Contrato del reporte

El archivo generado será `data/output/tabla_reporte_bot.csv`. Cada fila
representará un reseteo completado correctamente, no cada línea del log.

| Columna | Origen en el log | Motivo |
|---|---|---|
| `operation_id` | `[operation_Id=...]` | Es el identificador único de la operación y evita duplicados. |
| `fecha_solicitud_utc` | Evento `HTTP Request` a `resetuser` | Indica cuándo el bot recibió la solicitud. |
| `fecha_reseteo_utc` | Respuesta de ADManager exitosa | Indica cuándo ADManager confirmó el reseteo. |
| `usuario_solicitante` | `sAMAccountName_requester` de la solicitud | Identifica quién solicitó el reseteo. |
| `usuario_reseteado` | `sAMAccountName` de la respuesta de ADManager | Identifica al usuario que ADManager confirmó haber reseteado. |
| `estado` | Regla del proceso | Tendrá el valor `exitoso`; hace explícito el resultado de la fila. |
| `archivo_origen` | Nombre del archivo procesado | Permite rastrear de qué log salió el registro. |

### Regla para considerar un reseteo exitoso

Una operación se incluirá solamente si, bajo el mismo `operation_Id`, aparece
una respuesta de ADManager con los tres indicadores siguientes:

```text
'reset': 'yes'
'statusMessage': 'Password reset successful.'
'status': '1'
```

Las operaciones con errores HTTP, respuestas incompletas o incidencias creadas
por el bot no generarán una fila. Esto evita reportar una solicitud como si se
hubiera completado.

### Idempotencia

Antes de añadir una fila, el programa comparará su `operation_id` contra los
que ya existen en el CSV. Si ya existe, no la volverá a escribir. Por tanto,
procesar el mismo archivo más de una vez conserva el mismo reporte.

## Alcance de la primera versión

- Procesar archivos `.log` ubicados en `data/raw/`.
- Generar y actualizar un único CSV en `data/output/`.
- Reportar únicamente reseteos exitosos de ADManager.

No se incluirán todavía una base de datos, interfaz gráfica, envío de correos
ni un reporte de errores separado. Podrán añadirse después si son necesarios.

## Uso

Desde la raíz del proyecto, indique la fecha del archivo que desea procesar:

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m reporte_bot --fecha 2026-09-01
```

El comando busca `data/raw/2026-09-01.log` y actualiza
`data/output/tabla_reporte_bot.csv`. Si se vuelve a ejecutar con el mismo log,
no agrega filas repetidas.

## Pruebas

Para comprobar el código y su formato:

```powershell
.\.venv\Scripts\ruff.exe check src tests
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Estado actual

Los logs de ejemplo ya fueron ubicados en `data/raw/`, se validó el criterio
de éxito, se creó el lector y se implementó la extracción de reseteos exitosos.
También se creó el escritor idempotente del CSV y la CLI que procesa un archivo
completo por fecha. La primera versión del proyecto ya cumple su objetivo.

## Estructura

```text
src/reporte_bot/  # Código fuente del programa.
tests/            # Pruebas automatizadas.
data/raw/         # Logs de entrada (ignorados por Git).
data/output/      # CSV generado (ignorado por Git).
notebooks/        # Exploración opcional; no ejecuta el proceso principal.
```
