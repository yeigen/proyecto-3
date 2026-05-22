# Verdad observada

## Qué contiene

Decisión metodológica sobre qué fuente se usa como verdad observada principal en Situación 3.

## Decisión

Para NO2, SO2 y O3 se usa el parquet SISAIRE/DAGMA-CVC:

- [Parquet horario DAGMA/CVC](../../../dagma/dagma_cvc_horario_raw.parquet)
- [Metadata de estaciones](../../../dagma/estaciones_metadata.csv)
- [Manifest ground truth](../../../dagma/manifest_ground_truth.json)

El Excel Cristian se conserva como fuente complementaria, no como reemplazo.

## Motivo

El cruce parquet vs Excel no muestra equivalencia estadística suficiente para mezclar ambas fuentes como una sola verdad observada. En NO2, combinar Yumbo y Univalle mezcla fuente y estación, lo que confunde la interpretación.

## Evidencias relacionadas

- [Correlación parquet vs Excel](../evidencias/dagma/sit3_dagma_excel_parquet_correlacion_variables.png)
- [NO2 combinado Yumbo-Univalle](../evidencias/dagma/sit3_dagma_no2_yumbo_univalle_combinado.png)

## Referencias

- [DAGMA/CVC](../fuentes/dagma-cvc.md)
- [Excel Cristian](../fuentes/excel-cristian.md)
- [Justificación cruce DAGMA Cristian](../DAGMA_JUSTIFICACION_CRUCE_CRISTIAN.md)
