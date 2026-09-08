# Bitácora de Reseteos

Proyecto para transformar los logs diarios del bot de reseteo de usuarios en
un reporte CSV claro, histórico e idempotente.

## Objetivo

Para una fecha dada, el programa leerá el archivo de log correspondiente,
identificará los reseteos de usuarios gestionados por ADManager y actualizará
un reporte CSV sin duplicar registros.

## Estructura

```text
src/reporte_bot/  # Código fuente del programa.
tests/            # Pruebas automatizadas.
data/raw/         # Logs de entrada.
data/output/      # CSV generado.
notebooks/        # Exploración previa de los datos.
```
