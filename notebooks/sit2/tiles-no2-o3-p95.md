# Regeneración de tiles NO2 y O3 p95

Notebook mínimo para regenerar `contaminacion_alta_NO2` y `ozono_anomalo` con pseudo-label fuerte `p95`, y unificar el dataset v4 con SO2 p99.

## Bloque 0 - Setup

```python
!pip install -q zarr
```

```python
import os
import random
import concurrent.futures
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from tqdm.auto import tqdm

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
```

## Bloque 1 - Rutas y fuentes

```python
ruta_fuentes = "/kaggle/input/datasets/juanjoseorozcolopez/geovision-fuentes"
ruta_modis = "/kaggle/input/datasets/edwardsx/modis-v2-panel"
ruta_tiles_v3 = "/kaggle/input/datasets/edwardsx/geovision-tiles-sit2/tiles-v3-so2-p99-2021-2024"
ruta_scl = "/kaggle/input/datasets/edwardsx/geovision-tiles-sit2/scl_por_escena.csv"

ruta_s2 = os.path.join(ruta_fuentes, "copernicus_s2_sr_harmonized", "panel.zarr")
ruta_s5p_no2 = os.path.join(ruta_fuentes, "copernicus_s5p_offl_l3_no2", "panel.zarr")
ruta_s5p_so2 = os.path.join(ruta_fuentes, "copernicus_s5p_offl_l3_so2", "panel.zarr")
ruta_s5p_o3 = os.path.join(ruta_fuentes, "copernicus_s5p_offl_l3_o3", "panel.zarr")
ruta_era5 = os.path.join(ruta_fuentes, "ecmwf_era5_hourly", "panel.zarr")
ruta_modis_zarr = os.path.join(ruta_modis, "panel.zarr")

ruta_salida = Path("/kaggle/working/geovision-no2-o3-p95-tiles")
ruta_v4 = Path("/kaggle/working/geovision-tiles-v4-gases-p95-so2-p99-2021-2024")
ruta_salida.mkdir(parents=True, exist_ok=True)
ruta_v4.mkdir(parents=True, exist_ok=True)
```

```python
ds_s2 = xr.open_zarr(ruta_s2, chunks="auto")
ds_no2 = xr.open_zarr(ruta_s5p_no2, chunks="auto")
ds_so2 = xr.open_zarr(ruta_s5p_so2, chunks="auto")
ds_o3 = xr.open_zarr(ruta_s5p_o3, chunks="auto")
ds_era5 = xr.open_zarr(ruta_era5, chunks="auto")
ds_modis = xr.open_zarr(ruta_modis_zarr, chunks="auto")
df_scl = pd.read_csv(ruta_scl)
bands_s2 = list(ds_s2.coords["band"].values)
```

## Bloque 2 - Filtros y percentiles

```python
df_scl["fecha"] = pd.to_datetime(df_scl["time_s2"].str.split("T").str[0], format="%Y%m%d")
df_scl_validas = df_scl[(df_scl["fecha"] >= "2021-01-01") & (df_scl["fecha"] <= "2024-12-31") & (df_scl["scl_pct"] >= 0.30)].copy()
df_scl_validas["fecha_s2_dt"] = pd.to_datetime(df_scl_validas["time_s2"].str.split("_").str[0], format="%Y%m%dT%H%M%S")

ds_no2 = ds_no2.sel(time=slice("20210101", "20241231T235959"))
ds_so2 = ds_so2.sel(time=slice("20210101", "20241231T235959"))
ds_o3 = ds_o3.sel(time=slice("20210101", "20241231T235959"))

ds_no2["data"] = ds_no2["data"].where(ds_no2["data"].isel(band=2) < 0.7)
ds_so2["data"] = ds_so2["data"].where(ds_so2["data"].isel(band=1) < 0.7)
ds_o3["data"] = ds_o3["data"].where((ds_o3["data"].isel(band=1) < 0.7) & (ds_o3["data"].isel(band=0) > 0.0))

tiempos_era5 = pd.to_datetime(ds_era5["time"].values, format="%Y%m%dT%H")
ds_era5 = ds_era5.assign_coords(time=tiempos_era5).sel(time=slice("2021-01-01", "2024-12-31T23:59:59"))

ds_modis = ds_modis.sel(time=slice("A2021001", "A2024366"))
ds_modis = ds_modis.assign_coords(time=pd.to_datetime([str(t)[1:] for t in ds_modis["time"].values], format="%Y%j"))
```

```python
def mapear_tiempos_s5p(ds, nombre):
    serie = ds["data"].isel(band=0).mean(dim=["x", "y"], skipna=True)
    df_temp = serie.to_dataframe(name=nombre).dropna().reset_index()
    df_temp["fecha"] = pd.to_datetime(df_temp["time"].astype(str).str.split("_").str[0], format="%Y%m%dT%H%M%S")
    return df_temp[["time", "fecha", nombre]]

df_t_no2 = mapear_tiempos_s5p(ds_no2, "no2")
df_t_so2 = mapear_tiempos_s5p(ds_so2, "so2")
df_t_o3 = mapear_tiempos_s5p(ds_o3, "o3")

NO2_UMBRAL = float(df_t_no2["no2"].quantile(0.95))
O3_UMBRAL = float(df_t_o3["o3"].quantile(0.95))

print(f"NO2 p95: {NO2_UMBRAL:.8f}")
print(f"O3 p95: {O3_UMBRAL:.8f}")
```

## Bloque 3 - Funciones

```python
TILE_SIZE = 64
SCL_TILE_MIN = 0.30
N_OBJETIVO = 230
MAX_INTENTOS = 30000
WORKERS = 24

def extraer_tile_s2(escena, y0, x0):
    return escena["data"].isel(y=slice(y0, y0 + TILE_SIZE), x=slice(x0, x0 + TILE_SIZE)).values.astype("float32")

def calcular_indices_tile(tile):
    red = tile[bands_s2.index("B4")]
    nir = tile[bands_s2.index("B8")]
    swir = tile[bands_s2.index("B11")]
    scl = tile[bands_s2.index("SCL")]
    ndvi = np.nanmean((nir - red) / (nir + red + 1e-6))
    ndbi = np.nanmean((swir - nir) / (swir + nir + 1e-6))
    scl_pct = np.isin(scl, [4, 5, 6, 7]).mean()
    return float(ndvi), float(ndbi), float(scl_pct)

def muestrear_tile_valido(escena, intento):
    rng = np.random.default_rng(SEED + intento)
    ny, nx = escena.sizes["y"], escena.sizes["x"]
    for _ in range(50):
        y0 = int(rng.integers(0, ny - TILE_SIZE))
        x0 = int(rng.integers(0, nx - TILE_SIZE))
        tile = extraer_tile_s2(escena, y0, x0)
        ndvi, ndbi, scl_pct = calcular_indices_tile(tile)
        if scl_pct >= SCL_TILE_MIN and np.isfinite(ndvi) and np.isfinite(ndbi):
            return tile, float(escena["y"].values[y0 + TILE_SIZE // 2]), float(escena["x"].values[x0 + TILE_SIZE // 2]), ndvi, ndbi, scl_pct
    return None

def extraer_punto_s5p(ds, lat, lon, time_value, ventana=1):
    ds_time = ds.sel(time=time_value)
    iy = int(np.abs(ds_time["y"].values - lat).argmin())
    ix = int(np.abs(ds_time["x"].values - lon).argmin())
    bloque = ds_time["data"].isel(band=0, y=slice(max(0, iy - ventana), iy + ventana + 2), x=slice(max(0, ix - ventana), ix + ventana + 2)).values
    return float(np.nanmean(bloque)) if np.isfinite(bloque).any() else np.nan

def extraer_s5p_cercano(ds, df_tiempos, lat, lon, fecha_s2):
    candidatos = df_tiempos[(df_tiempos["fecha"] - pd.Timestamp(fecha_s2)).abs() <= pd.Timedelta(days=1)].copy()
    if candidatos.empty:
        return np.nan
    candidatos["delta"] = (candidatos["fecha"] - pd.Timestamp(fecha_s2)).abs()
    for _, fila in candidatos.sort_values("delta").iterrows():
        valor = extraer_punto_s5p(ds, lat, lon, fila["time"])
        if np.isfinite(valor):
            return valor
    return np.nan

def extraer_s5p_tile(lat, lon, fecha_s2):
    return (
        extraer_s5p_cercano(ds_no2, df_t_no2, lat, lon, fecha_s2),
        extraer_s5p_cercano(ds_so2, df_t_so2, lat, lon, fecha_s2),
        extraer_s5p_cercano(ds_o3, df_t_o3, lat, lon, fecha_s2),
    )

def extraer_era5_tile(lat, lon, fecha_s2):
    valores = ds_era5.sel(time=pd.Timestamp(fecha_s2).round("h"), y=lat, x=lon, method="nearest")["data"].values.astype("float32")
    return dict(zip(["era5_T2m", "era5_Td2m", "era5_u10", "era5_v10", "era5_BLH", "era5_RH850", "era5_psurf", "era5_precip"], map(float, valores)))

def extraer_modis_valor(lat, lon, fecha_s2, band_idx):
    fecha_base = pd.Timestamp(fecha_s2).normalize()
    for d in sorted(range(-3, 4), key=abs):
        fecha = fecha_base + pd.Timedelta(days=d)
        if np.datetime64(fecha) not in ds_modis["time"].values:
            continue
        ds_time = ds_modis.sel(time=fecha)
        iy = int(np.abs(ds_time["y"].values - lat).argmin())
        ix = int(np.abs(ds_time["x"].values - lon).argmin())
        bloque = ds_time["data"].isel(band=band_idx, y=slice(max(0, iy - 2), iy + 3), x=slice(max(0, ix - 2), ix + 3)).values
        if np.isfinite(bloque).any():
            return float(np.nanmean(bloque))
    return np.nan

def extraer_modis_tile(lat, lon, fecha_s2):
    return {"modis_AOD_047": extraer_modis_valor(lat, lon, fecha_s2, 0), "modis_AOD_055": extraer_modis_valor(lat, lon, fecha_s2, 1), "modis_WV": extraer_modis_valor(lat, lon, fecha_s2, 2)}
```

## Bloque 4 - Extracción NO2 y O3

```python
def intentar_extraccion(intento, objetivo, umbral, clase, texto_base):
    try:
        fila = df_scl_validas.sample(1, random_state=SEED + intento).iloc[0]
        time_s2 = fila["time_s2"]
        fecha_s2 = fila["fecha_s2_dt"]
        muestra = muestrear_tile_valido(ds_s2.sel(time=time_s2), intento)
        if muestra is None:
            return None

        tile, lat, lon, ndvi, ndbi, scl_pct = muestra
        no2, so2, o3 = extraer_s5p_tile(lat, lon, fecha_s2)
        valor = {"no2": no2, "o3": o3}[objetivo]
        if not np.isfinite(valor) or valor < umbral:
            return None

        meta = {
            "clase": clase,
            "time_s2": time_s2,
            "fecha_s2": fecha_s2,
            "lat": lat,
            "lon": lon,
            "ndvi": ndvi,
            "ndbi": ndbi,
            "scl_pct": scl_pct,
            "no2": no2,
            "so2": so2,
            "o3": o3,
            "texto": f"{texto_base}, {objetivo.upper()}={valor:.8f}.",
            f"umbral_{objetivo}": umbral,
            f"percentil_{objetivo}": 95,
            **extraer_era5_tile(lat, lon, fecha_s2),
            **extraer_modis_tile(lat, lon, fecha_s2),
        }
        return tile, meta
    except Exception:
        return None

def extraer_clase(objetivo, umbral, clase, texto_base):
    tiles, metas = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futuros = [executor.submit(intentar_extraccion, i, objetivo, umbral, clase, texto_base) for i in range(MAX_INTENTOS)]
        for futuro in tqdm(concurrent.futures.as_completed(futuros), total=MAX_INTENTOS, desc=clase):
            resultado = futuro.result()
            if resultado is None:
                continue
            tile, meta = resultado
            tiles.append(tile)
            metas.append(meta)
            tqdm.write(
                f"Candidato válido {len(tiles)}/{N_OBJETIVO} | "
                f"{objetivo.upper()}={meta[objetivo]:.8f} | "
                f"NDVI={meta['ndvi']:.3f} | "
                f"NDBI={meta['ndbi']:.3f}"
            )
            if len(tiles) >= N_OBJETIVO:
                for f in futuros:
                    f.cancel()
                break
    assert len(tiles) >= N_OBJETIVO, f"No hay suficientes tiles para {clase}"
    df_meta = pd.DataFrame(metas[:N_OBJETIVO])
    arr = np.stack(tiles[:N_OBJETIVO]).astype("float32")
    return df_meta, arr
```

```python
df_no2, tiles_no2 = extraer_clase(
    "no2",
    NO2_UMBRAL,
    "contaminacion_alta_NO2",
    "Zona con NO2 alto p95 por columna troposférica Sentinel-5P",
)

df_o3, tiles_o3 = extraer_clase(
    "o3",
    O3_UMBRAL,
    "ozono_anomalo",
    "Zona con O3 anómalo p95 por columna satelital Sentinel-5P",
)
```

## Bloque 5 - Guardado NO2 y O3

```python
df_no2.to_parquet(ruta_salida / "tiles_meta_no2_p95.parquet", index=False)
np.savez_compressed(ruta_salida / "tiles_train_no2_p95.npz", data=tiles_no2, bands=np.array(bands_s2))

df_o3.to_parquet(ruta_salida / "tiles_meta_o3_p95.parquet", index=False)
np.savez_compressed(ruta_salida / "tiles_train_o3_p95.npz", data=tiles_o3, bands=np.array(bands_s2))

print("Guardado NO2/O3 p95")
```

## Bloque 6 - Unificación v4

```python
df_v3 = pd.read_parquet(os.path.join(ruta_tiles_v3, "tiles_meta.parquet"))
npz_v3 = np.load(os.path.join(ruta_tiles_v3, "tiles_train.npz"), allow_pickle=True)
tiles_v3 = npz_v3["data"]
bands = npz_v3["bands"]

df_so2 = df_v3[df_v3["clase"] == "contaminacion_alta_SO2"].reset_index(drop=True)
df_urbano = df_v3[df_v3["clase"] == "suelo_urbano"].reset_index(drop=True)
df_vegetacion = df_v3[df_v3["clase"] == "vegetacion_densa"].reset_index(drop=True)

idx_so2 = df_v3.index[df_v3["clase"] == "contaminacion_alta_SO2"].to_numpy()
idx_urbano = df_v3.index[df_v3["clase"] == "suelo_urbano"].to_numpy()
idx_vegetacion = df_v3.index[df_v3["clase"] == "vegetacion_densa"].to_numpy()

df_final = pd.concat([df_no2, df_so2, df_o3, df_urbano, df_vegetacion], ignore_index=True)
tiles_final = np.concatenate([tiles_no2, tiles_v3[idx_so2], tiles_o3, tiles_v3[idx_urbano], tiles_v3[idx_vegetacion]], axis=0)

df_final.to_parquet(ruta_v4 / "tiles_meta.parquet", index=False)
np.savez_compressed(ruta_v4 / "tiles_train.npz", data=tiles_final.astype("float32"), bands=bands)

print(df_final["clase"].value_counts())
print(tiles_final.shape)
print(ruta_v4)
```
