# Justificación: xee vs ToCloudStorage vs getDownloadURL

## Decisión: usar `xee` para ERA5 (y las demás fuentes salvo Sentinel-2)

### `Export.image.toCloudStorage()` — No conveniente

`ee.batch.Export.image.toCloudStorage()` exporta imágenes GeoTIFF individuales al bucket GCS, procesando del lado de GEE. Sin embargo:

1. **No produce Zarr**: Genera GeoTIFFs que luego requieren conversión a Zarr (descargar, leer con rioxarray, apilar, subir). Agrega un paso completo de post-procesamiento.

2. **Una tarea por imagen**: Para ERA5 (43,824 imágenes) se necesitarían 43,824 export tasks. GEE tiene cuotas de ~3,000 tareas concurrentes y cada una tarda 30s-2min en completarse. Tiempo estimado: **12-48 horas** solo en submit+poll, sin contar la conversión.

3. **Orquestación compleja**: Requiere código para: crear tareas, monitorear estado, manejar reintentos, esperar completación, luego descargar y convertir. Esencialmente reescribir el pipeline existente con un paso más.

4. **GEE rate limits**: GEE limita tasks a ~3,000/día en cuenta gratuita y ~10,000/día en accounts registradas. Para MODIS (151,558 imágenes) o S5P (25,000+) esto excede las cuotas.

5. **Resolución nativa obligada**: `toCloudStorage` no permite reescalar — exporta a la resolución nativa del pixel grid de GEE. Para ERA5 esto no es problema (0.25°), pero para S5P o MODIS podría generar archivos más grandes de lo necesario.

6. **No hay beneficio real para datos pequeños**: ERA5 sobre Cali es 2×2 píxeles × 8 bandas × 43K timestamps ≈ 5 MB. El overhead de submitir 43K tareas a GEE es órdenes de magnitud mayor que simplemente leer los datos con `xee`.

### `xee` — La solución óptima

`xee` (Xarray Earth Engine) abre ImageCollections directamente como `xarray.Dataset`:

- **Sin descarga intermedia**: Lee directamente desde los servidores GEE vía API, convierte a xarray on-the-fly.
- **Un solo paso**: `open_dataset` → `to_zarr`. Sin GeoTIFFs, sin conversión manual.
- **Chunking nativo**: Soporta `io_chunks` para controlar el tamaño de los chunks Dask/lazy loading.
- **Compresión y formato controlado**: El `to_zarr` permite `encoding`, `dtype`, `consolidated` — todo configurable.
- **Funciona para cualquier tamaño**: Para datasets pequeños (ERA5: 5 MB), se materializa todo en RAM. Para grandes, usa Dask chunks.

### Pipeline por fuente

| Fuente | Método | Justificación |
|--------|--------|---------------|
| **ERA5** | `xee` directo → `panel.zarr` | 5 MB total. Cabe en RAM. Un solo paso. |
| **S5P NO₂/SO₂/O₃** | `xee` directo → `panel.zarr` | ~200-270 MB por fuente. Cabe en RAM con Dask. |
| **MODIS** | `xee` streaming → `panel.zarr` | ~9 GB. Streaming con `io_chunks` y `to_zarr(mode='a')`. |
| **Sentinel-2** | Pipeline propio existente | 91 GB, GeoTIFFs por banda. `xee` no es viable: getDownloadURL maneja bandas individuales y resolución 10m. |

### Benchmark estimado ERA5

- **getDownloadURL (método anterior)**: ~7h para 43K imágenes × 50/batch → 877 batches, cada uno descarga 50 GeoTIFFs + convierte + sube Zarr.
- **xee (método nuevo)**: abierto como Dataset, seleccionar 8 bandas, escribir a Zarr. Estimado: **5-15 minutos**.
- **toCloudStorage**: 43K tasks × ~1min c/p = **~30 días**. Absurdo para 5 MB de datos.