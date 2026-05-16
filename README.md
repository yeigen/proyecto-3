# GeoVision-CLIP Cali

Panel satelital multi-fuente sobre Cali + corredor industrial Yumbo-Acopi para modelado de calidad del aire con CLIP + SAE + Kriging.

## Descripcion

Proyecto academico que construye un panel de datos satelitales y atmosfericos (2021-2026) combinando 6 fuentes de Google Earth Engine, almacenado en Google Cloud Storage y HuggingFace Hub. El panel alimenta modelos de interpolacion espacial de contaminantes via embeddings multimodales (CLIP) y autoencoders esparsos (SAE), con validacion contra estaciones DAGMA/SISAIRE.

**BBox**: `[-76.65, 3.30, -76.30, 3.65]` (~38x38 km)  
**Ventana**: 2021-01-01 → 2026-01-01  
**Volumen**: ~98 GiB en GCS  
**Fuentes**: Sentinel-5P (NO2/SO2/O3), Sentinel-2 MSI, ERA5 hourly, MODIS MAIAC AOD

## Arquitectura

```
google-earth/config.py (configuracion central)
    │
    ├── gcp/exportar_*.py     → GEE getDownloadURL() → GCS (GeoTIFF raw)
    ├── gcp/zarr/*.py         → GeoTIFF → Zarr 4D con Dask + GCS
    └── hugging-face/         → GCS staging local → HuggingFace Hub
```

## Fuentes de datos

| Dataset | Imagenes | Bandas | Peso GCS |
|---------|----------|--------|----------|
| Sentinel-2 MSI | 1,552 | 13 | 97.61 GiB |
| Sentinel-5P NO2 | 25,592 | 3 | 90.76 MiB |
| Sentinel-5P SO2 | 25,830 | 2 | 38.22 MiB |
| Sentinel-5P O3 | 25,717 | 2 | 70.14 MiB |
| ERA5 hourly | 34,499 | 8 | 114.63 MiB |
| MODIS MAIAC AOD | ~80,000 | 4 | 175.75 MiB |

## Estado actual

| Componente | Estado |
|-----------|--------|
| Exportacion GCS | 6 fuentes completas (raw + Zarr) |
| HuggingFace | 5 datasets pequeños sincronizados; S2 vive solo en GCS por peso |
| Situacion 1 | Casi cerrada (panel ≥ 50 GB, lossless verificado) |
| Situacion 2 | Por iniciar (GeoVision-CLIP + SAE) |

## Documentacion

- [`docs/DATASETS.md`](docs/DATASETS.md) — catalogo de fuentes con justificacion de bandas
- [`docs/JUSTIFICACIONES.md`](docs/JUSTIFICACIONES.md) — formato, exportacion, pesos y decisiones tecnicas
- [`docs/REFERENCIAS.md`](docs/REFERENCIAS.md) — indice de enlaces externos
- [`docs/conceptos/geotiff-vs-zarr.md`](docs/conceptos/geotiff-vs-zarr.md) — diseño de chunks y benchmarks

## Requisitos

- Python 3.12+
- Gestor de paquetes: uv
- Google Earth Engine API (autenticacion via `gcloud`)
- Google Cloud SDK + credenciales GCP (proyecto `proyecto-analitica-3-495618`)
- HuggingFace Hub token (repo `JuanJose0/proyecto-final`)

## Quickstart

```bash
git clone <repo-url>
cd proyecto-3
uv sync
# Configurar .env con HF_TOKEN
source .venv/bin/activate
python -c "from google.oauth2 import service_account; ..."
```

## Referencias

- [Google Earth Engine Python API](https://developers.google.com/earth-engine/guides/python_install)
- [Zarr Specification](https://zarr.readthedocs.io/)
- [xarray Documentation](https://docs.xarray.dev/)
- [HuggingFace Hub](https://huggingface.co/docs/huggingface_hub)
- [Sentinel-2 User Handbook (ESA)](https://sentinel.esa.int/documents/247904/685211/Sentinel-2_User_Handbook)
- [ERA5 Documentation (ECMWF)](https://confluence.ecmwf.int/display/CKB/ERA5%3A+data+documentation)
- [MODIS MCD19A2 (NASA LP DAAC)](https://lpdaac.usgs.gov/products/mcd19a2v061/)
- [TROPOMI ATBDs (KNMI)](https://sentiwiki.copernicus.eu/web/document-library#DocumentLibrary-S5P-RELEVANTDOCUMENTS)
