# Excel Cristian

## Qué contiene

Fuente complementaria SVCASC con variables adicionales como PM10, PM25, H2S, meteorología y Black Carbon.

## Uso en la situación 3

Se conserva como fuente auxiliar, pero no se usa como verdad observada principal para NO2, SO2 y O3 porque no es estadísticamente equivalente al parquet SISAIRE/DAGMA-CVC.

## Hallazgo clave

El cruce parquet vs Excel produjo 35,184 registros coincidentes, pero las correlaciones fueron bajas:

| Variable | Correlación r | Lectura |
|---|---:|---|
| O3 | 0.387 | Baja/moderada |
| SO2 | 0.091 | Muy débil |

## Evidencias relacionadas

- [Carga del Excel SVCASC](../evidencias/dagma/sit3_dagma_excel_svcasc_carga.png)
- [Cruce de estaciones](../evidencias/dagma/sit3_dagma_excel_parquet_cruce_estaciones.png)
- [Registros coincidentes](../evidencias/dagma/sit3_dagma_excel_parquet_registros_coincidentes.png)
- [Correlación parquet vs Excel](../evidencias/dagma/sit3_dagma_excel_parquet_correlacion_variables.png)

## Referencias

- [Verdad observada](../metodologia/verdad-observada.md)
- [Justificación cruce DAGMA Cristian](../DAGMA_JUSTIFICACION_CRUCE_CRISTIAN.md)
