# Referencias — GeoVision-CLIP Cali

Índice de enlaces externos del proyecto. Cada entrada describe brevemente qué contiene.

---

## Google Earth Engine

- [Earth Engine Python API Reference](https://developers.google.com/earth-engine/apidocs) — referencia completa de clases y métodos del SDK
- [Earth Engine Data Catalog](https://developers.google.com/earth-engine/datasets/catalog) — catálogo de todos los datasets disponibles
- [Python Installation Guide](https://developers.google.com/earth-engine/guides/python_install) — instalación y autenticación
- [Projections and Reprojection](https://developers.google.com/earth-engine/guides/projections) — manejo de proyecciones y escalas
- [google/earthengine-api (GitHub)](https://github.com/google/earthengine-api) — código fuente del SDK
- [Context7 GEE snippets](https://context7.com/google/earthengine-api/llms.txt) — consultas rápidas con snippets
- [Earth Engine Dataset Catalog (md)](https://context7.com/wybert/earthengine-dataset-catalog-md) — catálogo en markdown

## Sentinel-5P TROPOMI

- [TROPOMI Mission Page (ESA)](https://sentinels.copernicus.eu/web/sentinel/missions/sentinel-5p) — descripción del instrumento y la misión
- [Sentinel-5P OFFL L3 NO2 — GEE Catalog](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_NO2) — ficha del asset NO₂ L3
- [Sentinel-5P OFFL L3 SO2 — GEE Catalog](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_SO2) — ficha del asset SO₂ L3
- [Sentinel-5P OFFL L3 O3 — GEE Catalog](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_O3) — ficha del asset O₃ L3
- [ATBD documentos S5P](https://sentiwiki.copernicus.eu/web/document-library#DocumentLibrary-S5P-RELEVANTDOCUMENTS) — documentos técnicos del algoritmo DOAS
- [TROPOMI products and algorithms](https://sentinels.copernicus.eu/web/sentinel/technical-guides/sentinel-5p/products-algorithms) — guía técnica de productos
- [TROPOMI user guide](https://sentinels.copernicus.eu/web/sentinel/user-guides/sentinel-5p-tropomi) — guía de usuario

## Sentinel-2 MSI

- [Sentinel-2 SR Harmonized — GEE Catalog](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED) — ficha del asset L2A armonizado
- [Sentinel-2 User Handbook (ESA)](https://sentinel.esa.int/documents/247904/685211/Sentinel-2_User_Handbook) — manual de usuario
- [Sentinel-2 MSI Technical Guide](https://sentiwiki.copernicus.eu/web/s2-mission) — guía técnica de la misión

## MODIS MAIAC AOD

- [MCD19A2 Granules — GEE Catalog](https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MCD19A2_GRANULES) — ficha del asset MAIAC v6.1
- [MCD19A2 Product Page (LP DAAC)](https://lpdaac.usgs.gov/products/mcd19a2v061/) — página oficial del producto NASA
- [MAIAC ATBD (NASA Goddard)](https://atmosphere-imager.gsfc.nasa.gov/sites/default/files/ModAtmo/MAIAC_ATBD_v1.pdf) — algoritmo MAIAC

## ECMWF ERA5

- [ERA5 Hourly en GEE Data Catalog](https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_HOURLY) — ficha del asset ERA5 horario
- [ERA5 Single Levels (Copernicus CDS)](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels) — fuente original del reanálisis
- [ERA5 Data Documentation (ECMWF)](https://confluence.ecmwf.int/display/CKB/ERA5%3A+data+documentation) — documentación técnica del producto

## DAGMA / SISAIRE

- [SISAIRE — IDEAM](http://sisaire.ideam.gov.co) — sistema nacional de calidad del aire
- [Resolución 2254 de 2017 (Min. Ambiente)](https://www.minambiente.gov.co/wp-content/uploads/2021/10/resolucion-2254-de-2017.pdf) — niveles máximos permisibles en Colombia
- [DAGMA Cali](https://www.cali.gov.co/dagma/) — autoridad ambiental municipal

## Google Cloud Storage

- [Instalación del cliente Python](https://cloud.google.com/storage/docs/reference/libraries#client-libraries-install-python) — paquete `google-cloud-storage`
- [Python Storage API Reference](https://cloud.google.com/python/docs/reference/storage/latest) — referencia completa de la librería
- [Upload objects desde archivos](https://cloud.google.com/storage/docs/uploading-objects) — `blob.upload_from_filename()`
- [Upload objects desde memoria](https://cloud.google.com/storage/docs/uploading-objects-from-memory) — upload programático
- [Autenticación (ADC)](https://cloud.google.com/docs/authentication/application-default-credentials) — Application Default Credentials
- [googleapis/python-storage (GitHub)](https://github.com/googleapis/python-storage) — código fuente
- [Context7 GCS snippets](https://context7.com/googleapis/python-storage/llms.txt) — consultas rápidas
- [Consola GCS — fuentes-proyecto-3](https://console.cloud.google.com/storage/browser/fuentes-proyecto-3) — bucket del proyecto

## HuggingFace Hub

- [Bucket del proyecto](https://huggingface.co/buckets/yeigen/fuentes-proyecto-3) — `yeigen/fuentes-proyecto-3`
- [HuggingFace Buckets Guide](https://huggingface.co/docs/huggingface_hub/en/guides/buckets) — almacenamiento tipo S3 con Xet backend
- [hf CLI Reference](https://huggingface.co/docs/huggingface_hub/en/guides/cli) — comandos `hf buckets sync`, `cp`, `list`
- [HuggingFace Hub Python Library](https://huggingface.co/docs/huggingface_hub) — SDK para interacción programática

## Formatos y herramientas

- [GeoTIFF Specification (OGC)](https://docs.ogc.org/is/19-008r4/19-008r4.html) — especificación del formato
- [GDAL GeoTIFF Driver](https://gdal.org/drivers/raster/gtiff.html) — opciones de compresión y tiling
- [Cloud Optimized GeoTIFF (COG)](https://www.cogeo.org/) — formato source-of-truth del proyecto
- [Zarr v3 Specification](https://zarr-specs.readthedocs.io/en/latest/v3/core/v3.0.html) — especificación oficial
- [Zarr Python Documentation](https://zarr.readthedocs.io/en/stable/) — librería Python
- [xarray Documentation](https://docs.xarray.dev/) — librería N-dimensional con integración Zarr
- [xarray + Zarr Integration](https://docs.xarray.dev/en/stable/user-guide/io.html#zarr) — escritura streaming con Dask
- [Dask Delayed](https://docs.dask.org/en/stable/delayed.html) — lazy evaluation out-of-core
- [Dask Array](https://docs.dask.org/en/stable/array.html) — arrays N-dim que no caben en memoria
- [Blosc Compression Library](https://www.blosc.org/) — meta-compresor utilizado en Zarr
- [Bitshuffle filter](https://github.com/kiyo-masui/bitshuffle) — pre-filtro para mejorar ratios sobre float32
- [Zstd compression](https://github.com/facebook/zstd) — algoritmo de compresión utilizado
- [Pangeo](https://pangeo.io/) — comunidad cloud native geospatial

## Proyecto

- [PDF de la asignatura](../proyecto/ProyectoFinal_GeoVisionCLIP_Cali.pdf) — Situaciones 1, 2 y 3
