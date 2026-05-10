# Revisión de enlaces — docs/conceptos/geotiff-vs-zarr.md

**Fecha**: 2026-05-10
**Tarea**: Verificar y corregir enlaces falsos/broken en la documentación de GeoTIFF vs Zarr

## Resumen

Se revisaron los 11 enlaces en la sección 8 del documento `docs/conceptos/geotiff-vs-zarr.md`. 5 estaban rotos (HTTP 404), 6 funcionaban correctamente. Se reemplazaron los 5 enlaces rotos por URLs verificadas.

## Cambios realizados

### Archivo modificado

- `docs/conceptos/geotiff-vs-zarr.md` — 5 enlaces corregidos en la sección 8 (Referencias)

### Enlaces corregidos

| # | Enlace original (roto) | Enlace corregido | Motivo |
|---|---|---|---|
| 1 | `https://zarr.readthedocs.io/en/stable/spec/v2.html` | `https://zarr-specs.readthedocs.io/en/latest/` | Zarr-python movió las specs a un sitio independiente. El original retorna 404. |
| 6 | `https://github.com/kmjohnson1/bitshuffle` | `https://github.com/kiyo-masui/bitshuffle` | El repositorio kmjohnson1/bitshuffle fue eliminado/renombrado. El repo oficial es kiyo-masui/bitshuffle. |
| 8 | `https://xarray.dev/blog/zarr-everywhere` | `https://docs.xarray.dev/en/stable/user-guide/io.html#zarr` | El blog post fue removido del sitio. La documentación oficial de xarray contiene la misma información sobre integración Zarr. |
| 9 | `https://discourse.pangeo.io/t/stac-vs-zarr-when-to-use-which/3196` | `https://discourse.pangeo.io/` | El topic específico #3196 fue eliminado del discourse. Se enlaza a la página principal del foro. |
| 10 | `https://pangeo.io/cloud.html` | `https://pangeo.io/` | La página cloud.html ya no existe. El sitio principal cubre la infraestructura cloud de Pangeo. |

### Enlaces verificados (sin cambios)

| # | Enlace | Estado |
|---|---|---|
| 2 | `https://zarr-specs.readthedocs.io/en/latest/v3/core/v3.0.html` | HTTP 200 |
| 3 | `https://www.cogeo.org/` | HTTP 200 |
| 4 | `https://gdal.org/drivers/raster/gtiff.html` | HTTP 200 |
| 5 | `https://www.blosc.org/` | HTTP 200 |
| 7 | `https://github.com/facebook/zstd` | HTTP 200 |
| 11 | `../../proyecto/ProyectoFinal_GeoVisionCLIP_Cali.pdf` | Archivo local existe |

## Estado del proyecto

### Droplet (192.241.132.222)

- **Pipeline S2→Zarr activo**: ejecutándose desde 15:35 (nohup, no screen)
- **Progreso**: lote 22/311 (~7%) al momento de revisión
- **Destino**: `gs://fuentes-proyecto-3/copernicus_s2_sr_harmonized/panel.zarr/`
- **RAM**: 7.5/7.8 GiB usado (crítico pero estable)
- **Proceso**: PID 3187819, 65.6% CPU, 3.97 GiB RES
- **Batch size**: 5 timestamps, ~2.4 GB/batch, chunks (5,13,974,974)
- **Compresión**: blosc/zstd/c5/bitshuffle

### Bucket GCS

- **Bucket**: `gs://fuentes-proyecto-3` (proyecto `proyecto-analitica-3-495618`)
- Accesible desde el droplet (gsutil funcional)
- gcloud CLI no instalado localmente (solo en droplet)

### HuggingFace

- NO2 panel.zarr ya subido con chunks de 0.0.0.0 a 3.2.3.3
- Bucket HF: `yeigen/fuentes-proyecto-3`

## Verificación Situación 1 (PDF)

Comparación de requisitos vs implementación:

| Requisito PDF | Estado | Evidencia |
|---|---|---|
| Credenciales GEE + CDSE | Hecho | `google-earth/autenticacion/` |
| Pipeline descarga Dask/Spark | Hecho | `gcp/exportar_*.py` con GEE batch export |
| Recorte HARP S5P | Hecho | BBox [-76.65,3.30,-76.30,3.65] en todos los exports |
| Conversión Zarr | En progreso | S2 pipeline corriendo en droplet (22/311 batches) |
| Persistencia GCS | Hecho | `gs://fuentes-proyecto-3/` con 6 datasets |
| Manifest JSON + MD5 | Pendiente | Scripts listos, manifest se genera al finalizar |
| EDA 8+ visualizaciones | Hecho | `google-earth/imagenes-cali/imagenes-reales/` con PNG por fuente |
| Peso >= 50 GB | Cumplido | Solo S2 GeoTIFF = 77 GB; S5P ~254 GB; Total > 100 GB |

## Referencias

- [Zarr v2/v3 specs](https://zarr-specs.readthedocs.io/en/latest/)
- [xarray I/O docs (Zarr section)](https://docs.xarray.dev/en/stable/user-guide/io.html#zarr)
- [Pangeo community](https://pangeo.io/)
- [Pangeo discourse](https://discourse.pangeo.io/)
- [Bitshuffle GitHub](https://github.com/kiyo-masui/bitshuffle)
- [Zarr Python docs](https://zarr.readthedocs.io/en/stable/)
