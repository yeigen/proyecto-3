# Bandas por Dataset — GeoVision-CLIP Cali

> Justificación respaldada en Google Earth Engine Data Catalog oficial.
> 30 bandas incluidas de 360 disponibles (8.3%).

**Peso estimado raw (con BANDAS_UTILES):** ~238 GB
**Peso estimado en Zarr/LZ4:** ~50–100 GB
**Umbral del proyecto:** ≥ 50 GB → ✅ **CUMPLE**

---

## 1. COPERNICUS/S5P/OFFL/L3_NO2 — Sentinel-5P Dióxido de Nitrógeno

**Descripción:** Imágenes de alta resolución de concentraciones de NO₂ troposférico. El NO₂ es un gas traza producido por combustión de combustibles fósiles, quema de biomasa y procesos naturales. Principal contaminante asociado al tráfico vehicular.

| Propiedad | Valor |
|-----------|-------|
| Resolución | 1113 m (0.01°) |
| Revisita | Diaria (1–2 órbitas) |
| Sensor | TROPOMI / ESA Copernicus |
| Disponible desde | 2018-06-28 |
| Ventana del proyecto | **2021-01-01 → 2026-01-01** |
| Catálogo GEE | [COPERNICUS_S5P_OFFL_L3_NO2](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_NO2) |

### Bandas INCLUIDAS (3 de 12)

| Banda | Unidad | Justificación |
|-------|--------|--------------|
| `tropospheric_NO2_column_number_density` | mol/m² | Columna vertical troposférica. Variable principal para estimar contaminación superficial. |
| `NO2_column_number_density` | mol/m² | Columna vertical TOTAL (tropo + estratosfera). Permite derivar fracción troposférica y validar contra DAGMA. |
| `cloud_fraction` | 0–1 | Fracción de nubes. Filtro de calidad para el modelo. |

### Bandas EXCLUIDAS (9 de 12)

| Banda | Motivo de exclusión |
|-------|-------------------|
| `stratospheric_NO2_column_number_density` | NO₂ estratosférico (10–50 km). No afecta calidad del aire superficial. |
| `NO2_slant_column_number_density` | Columna inclinada sin corregir. Producto intermedio del algoritmo DOAS. |
| `tropopause_pressure` | Parámetro auxiliar del algoritmo, no concentración. |
| `absorbing_aerosol_index` | Producto de aerosoles (familia AER_AI), no de NO₂. |
| `sensor_altitude` | Geometría de la órbita. |
| `sensor_azimuth_angle` | Geometría del satélite. |
| `sensor_zenith_angle` | Geometría del satélite. |
| `solar_azimuth_angle` | Geometría solar. |
| `solar_zenith_angle` | Geometría solar. |

---

## 2. COPERNICUS/S5P/OFFL/L3_SO2 — Sentinel-5P Dióxido de Azufre

**Descripción:** Imágenes de SO₂ atmosférico. Proviene de fuentes antropogénicas (industria, refinación) y naturales (volcanes). Afecta la salud respiratoria y contribuye a la formación de aerosoles de sulfato.

| Propiedad | Valor |
|-----------|-------|
| Resolución | 1113 m (0.01°) |
| Revisita | Diaria |
| Sensor | TROPOMI / ESA Copernicus |
| Disponible desde | 2018-12-05 |
| Ventana del proyecto | **2021-01-01 → 2026-01-01** |
| Catálogo GEE | [COPERNICUS_S5P_OFFL_L3_SO2](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_SO2) |

### Bandas INCLUIDAS (2 de 10)

| Banda | Unidad | Justificación |
|-------|--------|--------------|
| `SO2_column_number_density` | mol/m² | Columna vertical de SO₂ a nivel del suelo (técnica DOAS). Variable principal. |
| `cloud_fraction` | 0–1 | Control de calidad por nubosidad. |

### Bandas EXCLUIDAS (8 de 10)

| Banda | Motivo de exclusión |
|-------|-------------------|
| `SO2_slant_column_number_density` | Columna inclinada cruda. Producto intermedio DOAS. |
| `SO2_column_number_density_amf` | Air Mass Factor. Factor de corrección, no concentración. |
| `SO2_column_number_density_15km` | SO₂ a 15 km altitud. Para plumas volcánicas, no contaminación superficial. |
| `absorbing_aerosol_index` | Producto de aerosoles (par 340/380 nm), no de SO₂. |
| `sensor_azimuth_angle` | Geometría del satélite. |
| `sensor_zenith_angle` | Geometría del satélite. |
| `solar_azimuth_angle` | Geometría solar. |
| `solar_zenith_angle` | Geometría solar. |

---

## 3. COPERNICUS/S5P/OFFL/L3_O3 — Sentinel-5P Ozono

**Descripción:** Columna total de ozono. En la estratosfera protege de radiación UV. En la troposfera es un contaminante nocivo y gas de efecto invernadero.

| Propiedad | Valor |
|-----------|-------|
| Resolución | 1113 m (0.01°) |
| Revisita | Diaria |
| Sensor | TROPOMI / ESA Copernicus (algoritmo GODFIT) |
| Disponible desde | 2018-09-08 |
| Ventana del proyecto | **2021-01-01 → 2026-01-01** |
| Catálogo GEE | [COPERNICUS_S5P_OFFL_L3_O3](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_O3) |

### Bandas INCLUIDAS (2 de 7)

| Banda | Unidad | Justificación |
|-------|--------|--------------|
| `O3_column_number_density` | mol/m² | Columna total de O₃ (algoritmo GODFIT). Variable principal. |
| `cloud_fraction` | 0–1 | Control de calidad. |

### Bandas EXCLUIDAS (5 de 7)

| Banda | Motivo de exclusión |
|-------|-------------------|
| `O3_effective_temperature` | Parámetro interno del algoritmo GODFIT. No es una medición atmosférica independiente. |
| `sensor_azimuth_angle` | Geometría del satélite. |
| `sensor_zenith_angle` | Geometría del satélite. |
| `solar_azimuth_angle` | Geometría solar. |
| `solar_zenith_angle` | Geometría solar. |

---

## 4. COPERNICUS/S2_SR_HARMONIZED — Sentinel-2 MSI Surface Reflectance

**Descripción:** Reflectancia de superficie (Level-2A) armonizada. 13 bandas espectrales desde el visible hasta SWIR. Proporciona covariables ópticas de alta resolución: NDVI, índices urbanos, textura, sombra.

| Propiedad | Valor |
|-----------|-------|
| Resolución | 10 m (B2–B4, B8), 20 m (B5–B7, B8A, B11–B12), 60 m (B1, B9) |
| Revisita | 5 días |
| Sensor | MSI / ESA Copernicus |
| Disponible desde | 2017-03-28 |
| Ventana del proyecto | **2021-01-01 → 2026-01-01** |
| Catálogo GEE | [COPERNICUS_S2_SR_HARMONIZED](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED) |

### Bandas INCLUIDAS (13 de 26)

| Banda | Res. | Justificación |
|-------|------|--------------|
| `B1` | 60m | Aerosol costero. Corrección atmosférica. |
| `B2` | 10m | Azul. Dispersión atmosférica. |
| `B3` | 10m | Verde. Vegetación sana. |
| `B4` | 10m | Rojo. Clorofila, NDVI. |
| `B5` | 20m | Red Edge 1. Transición vegetación. |
| `B6` | 20m | Red Edge 2. Estrés vegetal. |
| `B7` | 20m | Red Edge 3. Continuo borde rojo. |
| `B8` | 10m | NIR. Reflectancia de vegetación sana. |
| `B8A` | 20m | NIR estrecho. Menos afectado por vapor de agua. |
| `B9` | 60m | Vapor de agua. Humedad atmosférica. |
| `B11` | 20m | SWIR 1. Humedad del suelo. |
| `B12` | 20m | SWIR 2. Contenido de agua y minerales. |
| `SCL` | 20m | Clasificación de escena (nube, sombra, vegetación, suelo, agua). |

> **Nota:** El PDF pide "13 bandas (B2–B12)". B2–B12 son 11 bandas. B1 y SCL completan 13. B10 no existe en Sentinel-2 harmonizado.

### Bandas EXCLUIDAS (13 de 26)

| Banda | Motivo de exclusión |
|-------|-------------------|
| `AOT` | Subproducto de corrección atmosférica, no reflectancia. |
| `WVP` | Columna de vapor de agua. Subproducto atmosférico. |
| `TCI_R`, `TCI_G`, `TCI_B` | Imagen RGB pre-renderizada. Producto de visualización, no científico. |
| `MSK_CLDPRB` | Máscara probabilística de nubes. Redundante con QA60. |
| `MSK_SNWPRB` | Máscara probabilística de nieve. Redundante. |
| `QA10`, `QA20` | Banderas de calidad. No son variables geofísicas. |
| `MSK_CLASSI_OPAQUE` | Clasificación de nubes opacas. Redundante. |
| `MSK_CLASSI_CIRRUS` | Clasificación de nubes cirrus. Redundante. |
| `MSK_CLASSI_SNOW_ICE` | Clasificación de nieve/hielo. Redundante. |

---

## 5. ECMWF/ERA5/HOURLY — ERA5 Reanálisis Atmosférico Horario

**Descripción:** Reanálisis climático global de 5ª generación del ECMWF. Combina modelos con observaciones para estimaciones horarias de variables atmosféricas. Datos en niveles simples (2D) desde 1940.

> ⚠️ **Nota importante:** El PDF menciona "ERA5-Land (9 km)", pero ERA5-Land **no contiene** Boundary Layer Height (BLH) ni Relative Humidity (RH). Usamos ERA5 atmosférico (27.8 km) que **sí** contiene ambas. La RH a 2m adicional se puede derivar con Magnus desde `temperature_2m + dewpoint_temperature_2m`.

| Propiedad | Valor |
|-----------|-------|
| Resolución | 27830 m (0.25°) |
| Periodicidad | Horaria |
| Fuente | ECMWF / Copernicus C3S |
| Disponible desde | 1940-01-01 |
| Ventana del proyecto | **2021-01-01 → 2026-01-01** |
| Catálogo GEE | [ECMWF_ERA5_HOURLY](https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_HOURLY) |

### Bandas INCLUIDAS (8 de 292)

| Banda | Unidad | Justificación |
|-------|--------|--------------|
| `temperature_2m` | K | Temperatura a 2 m. Meteorología fundamental para dispersión. |
| `dewpoint_temperature_2m` | K | Punto de rocío. Permite derivar RH con fórmula de Magnus. |
| `u_component_of_wind_10m` | m/s | Componente este del viento a 10 m. |
| `v_component_of_wind_10m` | m/s | Componente norte del viento a 10 m. |
| `boundary_layer_height` | m | Altura de capa límite (BLH). **Crítica** para modelado de dispersión. |
| `relative_humidity_850hPa` | % | Humedad relativa a ~1500 m. Indicador de formación de aerosoles secundarios. |
| `surface_pressure` | Pa | Presión en superficie. Influye en dispersión y correcciones de columna. |
| `total_precipitation` | m | Precipitación total. Lavado por lluvia = remoción de contaminantes. |

### Bandas EXCLUIDAS (284 de 292)

| Categoría | Ejemplos | Motivo |
|-----------|----------|--------|
| Variables oceánicas | `sea_surface_temperature`, `ice_temperature_layer_1-4` | Cali no es zona costera ni tiene hielo marino. |
| Nieve | `snow_depth`, `snow_albedo`, `snow_density`, `snowfall`, `snowmelt` | Cali no tiene nieve. |
| Lagos | `lake_*_temperature`, `lake_ice_depth`, `lake_mix_layer_depth` | Irrelevante para calidad del aire. |
| Radiación (20+) | `surface_net_solar/thermal_radiation`, `surface_*_shortwave/longwave_flux`, `surface_uv_radiation` | Variables radiativas no requeridas. |
| Viento a otras alturas | `u/v_component_of_wind_100m`, `wind_gust`, `neutral_wind` | El proyecto pide viento a 10m. |
| Precipitación por tipo | `convective/large_scale_precipitation/snowfall` | Usamos `total_precipitation` (suma). |
| Evaporación | `mean_evaporation_rate`, `potential_evaporation`, `snow_evaporation` | No requeridas. |
| Estrés y ondas | `turbulent_surface_stress`, `gravity_wave_stress/dissipation` | Dinámica fina no requerida. |
| Suelo | `soil_temperature_level_1-4`, `volumetric_soil_water_layer_1-4` | Variables de superficie terrestre, no atmosféricas. |
| Otras | `skin_temperature`, `mean_sea_level_pressure`, `forecast_albedo`, `runoff`, `surface_latent/sensible_heat_flux`, `leaf_area_index` | No requeridas por el proyecto. |

---

## 6. MODIS/061/MCD19A2_GRANULES — MODIS MAIAC Aerosol Optical Depth

**Descripción:** Producto de profundidad óptica de aerosoles (AOD) del algoritmo MAIAC sobre Terra + Aqua MODIS. Proxy de material particulado (PM₂.₅/PM₁₀) a 1 km.

| Propiedad | Valor |
|-----------|-------|
| Resolución | 927 m (~1 km) |
| Revisita | Diaria |
| Sensor | MODIS Terra + Aqua / NASA |
| Disponible desde | 2000-02-24 |
| Ventana del proyecto | **2021-01-01 → 2026-01-01** |
| Catálogo GEE | [MODIS_061_MCD19A2_GRANULES](https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MCD19A2_GRANULES) |

### Bandas INCLUIDAS (4 de 13)

| Banda | Unidad | Justificación |
|-------|--------|--------------|
| `Optical_Depth_047` | 0.001 | AOD a 0.47 μm (azul). Banda primaria de aerosoles. Proxy de PM. |
| `Optical_Depth_055` | 0.001 | AOD a 0.55 μm (verde). Validación cruzada independiente. |
| `Column_WV` | 0.001 | Columna de vapor de agua. Influye en aerosoles higroscópicos. |
| `AOD_QA` | bitfield | Banderas de calidad. Filtra pixeles con baja confianza (nubes, sombra). |

### Bandas EXCLUIDAS (9 de 13)

| Categoría | Motivo |
|-----------|--------|
| QA flags del algoritmo MAIAC | Banderas internas de calidad, máscaras de nube/nieve/agua. Redundantes con `AOD_QA`. |
| Parámetros del modelo de aerosoles | Fracción de modo fino/grueso. Internos del algoritmo. |
| Incertidumbre de la recuperación | Diagnóstico, no variable de entrada. |
| Ángulos de visión MODIS | Geometría del sensor. |

---

## Resumen

| # | Dataset | Incluidas | Disponibles | Ventana | Peso est. raw |
|---|---------|-----------|-------------|---------|---------------|
| 1 | S5P NO₂ | 3 | 12 | 2021–2026 | ~0.28 GB |
| 2 | S5P SO₂ | 2 | 10 | 2021–2026 | ~0.19 GB |
| 3 | S5P O₃ | 2 | 7 | 2021–2026 | ~0.19 GB |
| 4 | Sentinel-2 | 13 | 26 | 2021–2026 | ~232 GB |
| 5 | ERA5 | 8 | 292 | 2021–2026 | ~0.001 GB |
| 6 | MODIS MAIAC | 4 | 13 | 2021–2026 | ~1.62 GB |
| **Total** | | **30** | **360** | | **~238 GB raw** |

---

*Fuentes: Google Earth Engine Data Catalog, TROPOMI Product User Manuals (ESA), ERA5 Documentation (ECMWF/C3S), MAIAC ATBD (NASA).*
*Última actualización: 2026-05-07*
