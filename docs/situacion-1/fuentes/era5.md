# ERA5 horario

## Qué contiene

ERA5 aporta meteorología horaria para interpretar dispersión, mezcla atmosférica y condiciones de transporte de contaminantes.

## Uso en la situación 1

Se usan 8 variables:

- `temperature_2m`
- `dewpoint_temperature_2m`
- `u_component_of_wind_10m`
- `v_component_of_wind_10m`
- `boundary_layer_height`
- `relative_humidity_850hPa`
- `surface_pressure`
- `total_precipitation`

La variable más importante para dispersión es `boundary_layer_height` o BLH. En Cali cambia fuertemente durante el día: cerca de 66 m en la mañana y cerca de 607 m al mediodía.

## Evidencias relacionadas

- [Ciclo diurno ERA5](../evidencias/eda/era5/era5_ciclo_diurno.png)
- [Correlación de variables ERA5](../evidencias/eda/era5/era5_correlacion_variables.png)
- [Distribución temporal ERA5](../evidencias/eda/era5/era5_distribucion_temporal.png)
- [Capturas ERA5 Google Earth](../evidencias/fuentes/google-earth/cali/era5/)

## Referencias

- [ERA5 Hourly en Earth Engine](https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_HOURLY)
- [ERA5 data documentation ECMWF](https://confluence.ecmwf.int/display/CKB/ERA5%3A+data+documentation)
- [Reanálisis ERA5](../../conceptos/reanalisis-era5.md)
- [Humedad, temperatura y viento](../../conceptos/humedad-temperatura-viento.md)
- [Capa límite atmosférica](../../conceptos/capa-limite-blh.md)
