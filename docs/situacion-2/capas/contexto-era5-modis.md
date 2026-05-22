# Contexto ERA5 y MODIS

## Qué contiene

Variables meteorológicas y atmosféricas agregadas por tile para análisis y auditoría.

## ERA5

ERA5 aporta cobertura completa para todos los tiles:

- `era5_T2m`
- `era5_Td2m`
- `era5_u10`
- `era5_v10`
- `era5_BLH`
- `era5_RH850`
- `era5_psurf`
- `era5_precip`

## MODIS

MODIS aporta:

- `modis_AOD_047`
- `modis_AOD_055`
- `modis_WV`

AOD tiene cobertura baja por nubosidad. Vapor de agua (`modis_WV`) mantiene cobertura alta.

## Nota de calidad

La documentación final debe aclarar que el contexto MODIS confiable corresponde a la versión corregida con máscara, escala y filtro `h10v08`.

## Evidencias relacionadas

- [Cobertura MODIS por tiles](../evidencias/muestreo/tiles/cobertura-modis-tiles.png)
- [Distribuciones meta de tiles](../evidencias/muestreo/tiles/tiles_meta_distribuciones.png)

## Referencias

- [ERA5 en Situación 1](../../situacion-1/fuentes/era5.md)
- [MODIS MAIAC en Situación 1](../../situacion-1/fuentes/modis-maiac.md)
- [Auditoría de sesgos](../metodologia/auditoria-sesgos.md)
