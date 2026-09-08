# Bitácora de Reseteos

Proyecto para transformar los logs diarios del bot de reseteo de usuarios en un
reporte CSV claro, histórico e idempotente.

## Objetivo

Para una fecha dada, el programa leerá el archivo de log correspondiente,
identificará todas las llamadas al endpoint `users_admin/resetuser` y
actualizará `data/output/tabla_reporte_bot.csv` sin duplicar registros.

## Contrato del reporte

El archivo generado será `data/output/tabla_reporte_bot.csv`. Cada fila
representa una llamada a `resetuser`, exitosa o no, nunca una línea aislada.

| Columna | Origen en el log | Motivo |
|---|---|---|
| `timestamp` | Solicitud a `resetuser` | Momento de la operación. |
| `solicitante` y `target` | Parámetros de la solicitud | Usuarios involucrados. |
| `acción` y `sistema` | Regla del proceso | `reseteo de contraseña` y `ADManager`. |
| Nombres completos y oficinas | Perfiles de ADManager | Contexto de ambos usuarios. |
| `resultado` | Código y respuesta de ADManager | Mensaje humano del resultado final. |

### Regla para considerar un reseteo exitoso

El resultado se interpreta con el código retornado por `resetuser` y la
respuesta de ADManager. Por ejemplo, 404 identifica cuál usuario no existe,
403 explica la regla de permisos, 503 conserva el detalle de ADManager y 504
indica un timeout. El código HTTP no aparece como resultado final.

```text
'reset': 'yes'
'statusMessage': 'Password reset successful.'
'status': '1'
```

El resultado exitoso se confirma con las tres marcas siguientes:

### Idempotencia

Antes de añadir una fila, el programa compara todos sus campos contra los que
ya existen en el CSV. Si ya existe, no la vuelve a escribir.

## Alcance de la primera versión

- Procesar archivos `.log` ubicados en `data/input/`.
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

En Linux, con `uv` instalado, el equivalente es:

```bash
PYTHONPATH=src uv run python -m reporte_bot --fecha 2026-09-01
```

El comando busca `data/input/2026-09-01.log` y actualiza
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

Los logs de ejemplo ya fueron ubicados en `data/input/`. La CLI procesa todos
los resultados de `resetuser`, traduce las reglas de ADManager y actualiza el
CSV idempotente por fecha.

## Estructura

```text
src/reporte_bot/  # Código fuente del programa.
tests/            # Pruebas automatizadas.
data/input/       # Logs de entrada (ignorados por Git).
data/output/      # CSV generado (ignorado por Git).
notebooks/        # Exploración opcional; no ejecuta el proceso principal.
```
