# DAGMA/CVC

## Qué contiene

DAGMA/CVC es la verdad observada puntual del proyecto. No es una fuente satelital: son mediciones de estaciones de calidad del aire.

## Uso en la situación 1

El archivo principal es `dagma/dagma_cvc_horario_raw.parquet`. Contiene 107,291 registros horarios entre 2020 y 2024. El cruce útil con el panel satelital cubre 2021-2024.

Contaminantes:

- NO2: solo aparece en ESTACIÓN YUMBO dentro del parquet principal.
- SO2: aparece en seis estaciones.
- O3: aparece en ocho estaciones.

## Limitación principal

NO2 solo tiene verdad observada en Yumbo. Esto no invalida el panel, pero limita la validación espacial posterior para NO2.

## Evidencias relacionadas

- [Serie mensual por contaminante](../evidencias/eda/dagma/dagma_serie_temporal_media_contaminantes.png)
- [Serie mensual por estación](../evidencias/eda/dagma/dagma_serie_temporal_media_por_estacion.png)
- [Cobertura temporal DAGMA](../../situacion-3/evidencias/dagma/figuras/dagma_cobertura_temporal.png)
- [Estaciones frente a tile MGRS](../../situacion-3/evidencias/dagma/figuras/dagma_estaciones_vs_tile_mgrs.png)

## Referencias

- [SISAIRE IDEAM](http://sisaire.ideam.gov.co)
- [DAGMA Cali](https://www.cali.gov.co/dagma/)
- [Datos DAGMA locales](../../../dagma/)
- [Justificación cruce DAGMA](../../situacion-3/DAGMA_JUSTIFICACION_CRUCE_CRISTIAN.md)
