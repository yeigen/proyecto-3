# DAGMA/CVC

## Qué contiene

Fuente canónica de verdad observada para NO2, SO2 y O3 en Situación 3.

## Archivos

- [Parquet horario DAGMA/CVC](../../../dagma/dagma_cvc_horario_raw.parquet)
- [Metadata de estaciones](../../../dagma/estaciones_metadata.csv)
- [Manifest ground truth](../../../dagma/manifest_ground_truth.json)

## Uso en la situación 3

Se usa como verdad observada principal porque tiene esquema normalizado, trazabilidad y cobertura 2020-2024. El overlap útil con el panel satelital es 2021-2024.

## Evidencias relacionadas

- [Estructura del parquet](../evidencias/dagma/sit3_dagma_parquet_estructura.png)
- [Carga del parquet](../evidencias/dagma/sit3_dagma_parquet_carga_principal.png)
- [Estaciones DAGMA vs tiles MGRS](../evidencias/dagma/figuras/dagma_estaciones_vs_tile_mgrs.png)
- [Cobertura temporal](../evidencias/dagma/figuras/dagma_cobertura_temporal.png)

## Referencias

- [SISAIRE IDEAM](http://sisaire.ideam.gov.co)
- [DAGMA Cali](https://www.cali.gov.co/dagma/)
- [Verdad observada](../metodologia/verdad-observada.md)
- [Justificación cruce DAGMA Cristian](../DAGMA_JUSTIFICACION_CRUCE_CRISTIAN.md)
