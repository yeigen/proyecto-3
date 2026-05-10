# Referencias — GeoVision-CLIP Cali

Enlaces a documentacion oficial, catalogos, APIs y papers utilizados en el proyecto.
Recopilado: 2026-05-08.

---

## Google Earth Engine (GEE)

### API y SDK

- [Earth Engine Python API Reference](https://developers.google.com/earth-engine/apidocs) — referencia completa de clases y metodos
- [ee.Image.getDownloadURL](https://developers.google.com/earth-engine/apidocs/ee-image-getdownloadurl) — metodo principal de descarga sincrona
- [ee.Export (Batch)](https://developers.google.com/earth-engine/apidocs/ee-export) — exportacion asincrona a Drive, Cloud Storage, Asset
- [ee.ImageCollection.filterDate](https://developers.google.com/earth-engine/apidocs/ee-imagecollection-filterdate)
- [ee.ImageCollection.filterBounds](https://developers.google.com/earth-engine/apidocs/ee-imagecollection-filterbounds)
- [ee.Image.clip](https://developers.google.com/earth-engine/apidocs/ee-image-clip)
- [ee.Image.select](https://developers.google.com/earth-engine/apidocs/ee-image-select)
- [ee.Image.bandNames](https://developers.google.com/earth-engine/apidocs/ee-image-bandnames)
- [ee.Image.projection](https://developers.google.com/earth-engine/apidocs/ee-image-projection)
- [ee.Projection.nominalScale](https://developers.google.com/earth-engine/apidocs/ee-projection-nominalscale)
- [ee.Geometry.Rectangle](https://developers.google.com/earth-engine/apidocs/ee-geometry-rectangle)
- [ee.Initialize](https://developers.google.com/earth-engine/apidocs/ee-initialize)

### Guias

- [Python Installation Guide](https://developers.google.com/earth-engine/guides/python_install) — instalacion y autenticacion del entorno
- [Earth Engine Guides](https://developers.google.com/earth-engine/guides) — guias generales de la plataforma
- [Projections and Reprojection](https://developers.google.com/earth-engine/guides/projections) — como GEE maneja proyecciones y escalas

### Datasets Catalog

- [Earth Engine Data Catalog](https://developers.google.com/earth-engine/datasets/catalog) — catalogo completo de datasets disponibles

### Repositorio oficial

- [google/earthengine-api (GitHub)](https://github.com/google/earthengine-api) — codigo fuente del SDK Python
- [Context7 GEE snippets](https://context7.com/google/earthengine-api/llms.txt)

---

## ERA5 Hourly — ECMWF/ERA5/HOURLY

### Catalogos y documentacion

- [ERA5 Hourly en GEE Data Catalog](https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_HOURLY) — pagina oficial del dataset en Earth Engine
- [ERA5 Single Levels (Copernicus CDS)](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels) — fuente original del reanalisis
- [ERA5 Data Documentation (ECMWF)](https://confluence.ecmwf.int/display/CKB/ERA5%3A+data+documentation) — documentacion tecnica del producto ERA5
- [ERA5 vs ERA5-Land Comparison](https://confluence.ecmwf.int/display/CKB/ERA5-Land%3A+data+documentation) — diferencias entre ERA5 atmosferico y ERA5-Land

### Sobre la decision ERA5 vs ERA5-Land

El PDF de la asignatura pide ERA5-Land, pero ese dataset **no contiene `boundary_layer_height` ni `relative_humidity`** (es un downscale de superficie a 9 km). Usamos `ECMWF/ERA5/HOURLY` (atmosferico, 27.8 km) que si los contiene. Trade-off documentado en [`DATASETS.md`](DATASETS.md#5-ecmwf-era5--reanalisis-atmosferico-horario) y [`CRUCE_FUENTES_PDF.txt`](CRUCE_FUENTES_PDF.txt).

### Bandas seleccionadas (8 de 292 disponibles)

| Banda | Unidad | Proposito |
|-------|--------|-----------|
| `temperature_2m` | K | Temperatura — dispersion atmosferica |
| `dewpoint_temperature_2m` | K | Punto de rocio — derivacion de RH (Magnus) |
| `u_component_of_wind_10m` | m/s | Viento este (transporte horizontal) |
| `v_component_of_wind_10m` | m/s | Viento norte |
| `boundary_layer_height` | m | BLH — critica para modelado de dispersion |
| `relative_humidity_850hPa` | % | RH a ~1500 m — formacion de aerosoles secundarios |
| `surface_pressure` | Pa | Presion — correccion de columnas |
| `total_precipitation` | m | Lavado por lluvia (remocion de contaminantes) |

### Propiedades del dataset

- **Resolucion**: 27,830 m (0.25° — grilla nativa)
- **Cadencia**: 1 hora
- **Cobertura**: global
- **Disponible desde**: 1940-01-01
- **Parametros de media**: promediados sobre la hora que termina en la fecha/hora de validez

---

## Google Cloud Storage (GCS)

### Python Client Library

- [Instalacion del cliente Python](https://cloud.google.com/storage/docs/reference/libraries#client-libraries-install-python)
- [Python Storage API Reference](https://cloud.google.com/python/docs/reference/storage/latest) — referencia completa de la libreria
- [Upload objects desde archivos](https://cloud.google.com/storage/docs/uploading-objects) — `blob.upload_from_filename()`
- [Upload objects desde memoria](https://cloud.google.com/storage/docs/uploading-objects-from-memory) — `blob.upload_from_string()`, `blob.upload_from_file()`
- [Download objects](https://cloud.google.com/storage/docs/downloading-objects)
- [Autenticacion (ADC)](https://cloud.google.com/docs/authentication/application-default-credentials)

### Repositorio y snippets

- [googleapis/python-storage (GitHub)](https://github.com/googleapis/python-storage) — codigo fuente
- [Context7 GCS snippets](https://context7.com/googleapis/python-storage/llms.txt)

### Bucket del proyecto

- [Consola GCS — gs://fuentes-proyecto-3](https://console.cloud.google.com/storage/browser/fuentes-proyecto-3)
- Proyecto GCP: `proyecto-analitica-3-495618`

---

## Sentinel-5P TROPOMI

### NO2

- [Sentinel-5P OFFL L3 NO2 — GEE Catalog](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_NO2)
- [TROPOMI Mission Page (ESA)](https://sentinels.copernicus.eu/web/sentinel/missions/sentinel-5p)
- [ATBD NO2 (KNMI)](https://sentiwiki.copernicus.eu/web/document-library#DocumentLibrary-S5P-RELEVANTDOCUMENTS)

### SO2

- [Sentinel-5P OFFL L3 SO2 — GEE Catalog](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_SO2)
- [TROPOMI SO2 ATBD](https://sentinels.copernicus.eu/web/sentinel/technical-guides/sentinel-5p/products-algorithms)

### O3

- [Sentinel-5P OFFL L3 O3 — GEE Catalog](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_O3)
- [TROPOMI O3 ATBD](https://sentinels.copernicus.eu/web/sentinel/user-guides/sentinel-5p-tropomi)

---

## Sentinel-2 MSI

- [Sentinel-2 SR Harmonized — GEE Catalog](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED)
- [Sentinel-2 User Handbook (ESA)](https://sentinel.esa.int/documents/247904/685211/Sentinel-2_User_Handbook)
- [Sentinel-2 MSI Technical Guide](https://sentiwiki.copernicus.eu/web/s2-mission)

---

## MODIS MAIAC AOD

- [MCD19A2 Granules — GEE Catalog](https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MCD19A2_GRANULES)
- [MCD19A2 Product Page (LP DAAC)](https://lpdaac.usgs.gov/products/mcd19a2v061/)
- [MAIAC ATBD (NASA Goddard)](https://atmosphere-imager.gsfc.nasa.gov/sites/default/files/ModAtmo/MAIAC_ATBD_v1.pdf)

---

## DAGMA / SISAIRE (Ground Truth)

- [SISAIRE — IDEAM](http://sisaire.ideam.gov.co) — datos de calidad del aire en Colombia
- [Resolucion 2254 de 2017 (Min. Ambiente)](https://www.minambiente.gov.co/wp-content/uploads/2021/10/resolucion-2254-de-2017.pdf) — niveles permisibles
- [DAGMA Cali](https://www.cali.gov.co/dagma/)

---

## HuggingFace Hub — Almacenamiento del panel

### Bucket vs Dataset Repo

HuggingFace ofrece dos formas de almacenar datos:

| | **Bucket** | **Dataset Repo** |
|---|---|---|
| Almacenamiento | Objeto puro (S3-like), Xet backend | Git + LFS |
| Versionado | No ( mutable, sin historial) | Si (commits, branches, tags) |
| Limite archivos | Sin limite practico | ~10,000 por carpeta |
| Dataset Viewer | No | Si |
| URL de acceso | `hf://buckets/namespace/name` | `hf://datasets/namespace/name` |
| Comando upload | `hf buckets sync` | `hf upload` / `upload_large_folder` |
| Ideal para | Zarr grandes, artefactos, checkpoints | Datasets con tarjeta, versionado |

Usamos **Bucket** para los zarr del panel porque:
1. Sin limite de 10K archivos/carpeta (S2 tendra ~5,000 chunks)
2. Upload resumible y mas rapido con `hf buckets sync`
3. Sin overhead de git LFS (no necesita squash_history)
4. Acceso directo via URL publica

### Bucket del proyecto

- **Bucket**: [`yeigen/fuentes-proyecto-3`](https://huggingface.co/buckets/yeigen/fuentes-proyecto-3)
- **URL base**: `https://huggingface.co/buckets/yeigen/fuentes-proyecto-3`

### Documentacion

- [HuggingFace Buckets Guide](https://huggingface.co/docs/huggingface_hub/en/guides/buckets) — almacenamiento tipo S3 en HF con Xet backend
- [hf CLI Reference](https://huggingface.co/docs/huggingface_hub/en/guides/cli) — comando `hf buckets sync`, `hf buckets cp`, `hf buckets list`
- [XBDrive/Xet Storage](https://huggingface.co/docs/huggingface_hub/en/guides/buckets#xet-storage) — backend de deduplicacion por contenido
- [HuggingFace Hub Python Library](https://huggingface.co/docs/huggingface_hub) — SDK para interaccion programatica

### Comandos utiles

```bash
# Listar contenido del bucket
hf buckets list yeigen/fuentes-proyecto-3 -R -h

# Sincronizar staging local al bucket
hf buckets sync hugging-face/staging/ hf://buckets/yeigen/fuentes-proyecto-3

# Copiar un archivo al bucket
hf buckets cp ./archivo.zarr hf://buckets/yeigen/fuentes-proyecto-3/dataset/panel.zarr/

# Descargar del bucket al local
hf buckets sync hf://buckets/yeigen/fuentes-proyecto-3 ./data/
```

### Acceso a los datos

Los zarr se leen directamente desde el bucket HF con xarray/zarr:

```python
import xarray as xr
base = "https://huggingface.co/buckets/yeigen/fuentes-proyecto-3"
ds = xr.open_dataset(f"{base}/ecmwf_era5_hourly/panel.zarr", engine='zarr', consolidated=False)
```

---

## Formatos y herramientas

### GeoTIFF

- [GeoTIFF Specification (OGC)](https://docs.ogc.org/is/19-008r4/19-008r4.html)
- [GDAL GeoTIFF Driver](https://gdal.org/drivers/raster/gtiff.html)
- [Cloud Optimized GeoTIFF (COG)](https://www.cogeo.org/)
- [LZW Compression in TIFF](https://en.wikipedia.org/wiki/TIFF#Compression)

### Zarr

- [Zarr v3 Specification](https://zarr-specs.readthedocs.io/en/latest/v3/core/v3.0.html)
- [Zarr Python Documentation](https://zarr.readthedocs.io/en/stable/)
- [Zarr Chunking Tutorial](https://zarr.readthedocs.io/en/stable/tutorial.html#chunks) — estrategias de chunking para acceso eficiente
- [xarray + Zarr Integration](https://docs.xarray.dev/en/stable/user-guide/io.html#zarr) — escritura streaming con Dask

### Dask

- [Dask Delayed](https://docs.dask.org/en/stable/delayed.html) — lazy evaluation para datasets out-of-core
- [Dask Array](https://docs.dask.org/en/stable/array.html) — arrays N-dimensionales que no caben en memoria
- [Dask + xarray best practices](https://docs.xarray.dev/en/stable/user-guide/dask.html) — integracion Dask-xarray para datos geoespaciales

### Otros

- [xarray Documentation](https://docs.xarray.dev/)
- [Pangeo — Cloud Native Geospatial](https://pangeo.io/)
- [Blosc Compression Library](https://www.blosc.org/)
---

## Context7 (Consultas rapidas con snippets)

- [Earth Engine API](https://context7.com/google/earthengine-api/llms.txt)
- [Google Cloud Storage Python](https://context7.com/googleapis/python-storage/llms.txt)
- [Earth Engine Dataset Catalog (Markdown)](https://context7.com/wybert/earthengine-dataset-catalog-md)

---

## Proyecto

- [PDF de la asignatura](../proyecto/ProyectoFinal_GeoVisionCLIP_Cali.pdf) — Situaciones 1, 2, 3
- [Revision del proyecto (2026-05-08)](REVISION_2026-05-08.md)
