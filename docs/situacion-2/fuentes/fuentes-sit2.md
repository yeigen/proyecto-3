# Fuentes usadas en Situación 2

## Qué contiene

La Situación 2 reutiliza el panel construido en Situación 1 y lo convierte en un dataset de tiles para entrenamiento contrastivo.

## Fuentes

- Sentinel-2: imagen óptica base para los tiles.
- Sentinel-5P: pseudo-labels para NO2, SO2 y O3.
- ERA5: contexto meteorológico por tile.
- MODIS MAIAC: contexto de aerosoles y vapor de agua.
- DAGMA/CVC: estaciones usadas para clase urbana y auditoría puente.

## Uso en la situación 2

El modelo final CLIP usa solo bandas ópticas Sentinel-2. Las demás fuentes guían muestreo, contexto y auditorías; no entran como atajo directo al encoder visual final.

## Referencias

- [Situación 1](../../situacion-1/README.md)
- [Panel Zarr](../../situacion-1/capas/panel-zarr.md)
- [Muestreo Sit 2](../MUESTREO_SIT2.md)
- [Referencias Sit 2](../referencias.md)
