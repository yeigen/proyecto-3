# MODIS MAIAC

## Qué contiene

MODIS MAIAC aporta profundidad óptica de aerosoles y vapor de agua. Es una señal atmosférica útil, aunque no reemplaza mediciones superficiales de PM2.5 o PM10.

## Uso en la situación 1

Variables usadas:

- `Optical_Depth_047`
- `Optical_Depth_055`
- `Column_WV`
- `AOD_QA`

La versión confiable del panel es `panel_v3.zarr`, después de corregir tres problemas: máscara de `_FillValue`, escala `0.001` y filtro del tile MODIS `h10v08`.

## Hallazgo principal

La cobertura de AOD es baja por nubosidad tropical, pero el vapor de agua mantiene cobertura alta y queda como variable útil.

## Evidencias relacionadas

- [Mapa promedio MODIS corregido](../evidencias/eda/modis/v2/modis_mapa_promedio.png)
- [Cobertura efectiva MODIS](../evidencias/eda/modis/v2/modis_cobertura_efectiva.png)
- [Raw vs escalado MODIS](../evidencias/eda/modis/v2/modis_raw_vs_escalado.png)
- [Capturas MODIS MAIAC](../evidencias/fuentes/google-earth/cali/modis_maiact/)

## Referencias

- [MODIS MAIAC MCD19A2.061 en Earth Engine](https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MCD19A2_GRANULES)
- [MCD19A2 v061 LP DAAC](https://lpdaac.usgs.gov/products/mcd19a2v061/)
- [MAIAC ATBD NASA](https://atmosphere-imager.gsfc.nasa.gov/sites/default/files/ModAtmo/MAIAC_ATBD_v1.pdf)
- [Material particulado y AOD](../../conceptos/material-particulado-aod.md)
