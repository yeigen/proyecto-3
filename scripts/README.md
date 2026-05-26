# Scripts auxiliares

## descargar_hf.py

Descarga los 4 datasets satelitales desde HuggingFace Hub al cache local `data/hf-cache/`. Ejecutar después de clonar el repo o cuando se necesiten los paneles Zarr para EDA / Sit 3 local.

```bash
uv run python scripts/descargar_hf.py
```

**Variables requeridas** (en `.env`):
- `HF_TOKEN` — token con acceso al repo `yeigen/fuentes-proyecto-3`

**Datasets descargados**:
- `copernicus_s5p_offl_l3_no2/panel.zarr` (~20 MB) — NO2 troposférico TROPOMI
- `copernicus_s5p_offl_l3_o3/panel.zarr` (~70 MB) — O3 columnar
- `copernicus_s5p_offl_l3_so2/panel.zarr` (~40 MB) — SO2 vertical
- `ecmwf_era5_hourly/panel.zarr` (~115 MB) — ERA5 meteorológico

**NO se descarga Sentinel-2** (97 GB). S2 vive solo en GCS (`gs://fuentes-proyecto-3`) y Kaggle (`juanjoseorozcolopez/geovision-fuentes`). Sit 2/3 lo usa directo desde Kaggle.

**Para descargar solo algunos**:
```bash
uv run python scripts/descargar_hf.py --solo copernicus_s5p_offl_l3_no2,ecmwf_era5_hourly
```
