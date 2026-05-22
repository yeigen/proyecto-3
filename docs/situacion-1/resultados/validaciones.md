# Validaciones

## Qué contiene

Validaciones realizadas para asegurar que el panel de Situación 1 sea trazable y físicamente razonable.

## Validaciones principales

- Conversión GeoTIFF a Zarr verificada como bit-perfect en fuentes clave.
- Manifest generado con tamaño, conteo de archivos y hashes MD5.
- Rangos físicos revisados para Sentinel-5P, ERA5 y MODIS.
- MODIS corregido hasta obtener AOD físico.
- Pesos y conteos reconciliados entre Kaggle y manifest.

## Resultados destacados

| Fuente | Banda | Resultado |
|---|---|---|
| Sentinel-2 | B1, B4, B8, SCL | bit-perfect |
| Sentinel-5P NO2 | tropospheric_NO2 | ruido menor por float64 a float32 |
| ERA5 | temperature_2m | bit-perfect |

## Riesgos identificados

- Sentinel-2 tiene baja cobertura útil por nubosidad.
- NO2 en estaciones solo existe para Yumbo.
- O3 de Sentinel-5P es columna total, no ozono superficial.
- MODIS AOD tiene cobertura baja en zona tropical nublada.
- El BBox global del manifest conserva el BBox original del PDF, aunque las fuentes usan el BBox operativo.

## Referencias

- [Manifest técnico](../../../manifest/manifest_output/manifest.json)
- [Panel original de Situación 1](../SIT1_PANEL.md)
- [Justificaciones técnicas](../../JUSTIFICACIONES.md)
