# Regeneración de tiles SO2 p99

Notebook guía para regenerar solo la clase `contaminacion_alta_SO2` con pseudo-label fuerte `SO2 >= p99`, extracción paralela y diagnóstico contra `vegetacion_densa`.

## Bloque 0 - Setup

```python
!pip install -q zarr
```

```python
import os
import json
import random
import datetime
import subprocess
import concurrent.futures
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from tqdm.auto import tqdm

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
rng = np.random.default_rng(SEED)
```

## Bloque 1 - Rutas y apertura de fuentes

```python
ruta_fuentes = "/kaggle/input/datasets/juanjoseorozcolopez/geovision-fuentes"
ruta_modis = "/kaggle/input/datasets/edwardsx/modis-v2-panel"
ruta_scl = "/kaggle/input/datasets/edwardsx/geovision-tiles-sit2/scl_por_escena.csv"

ruta_s2 = os.path.join(ruta_fuentes, "copernicus_s2_sr_harmonized", "panel.zarr")
ruta_s5p_no2 = os.path.join(ruta_fuentes, "copernicus_s5p_offl_l3_no2", "panel.zarr")
ruta_s5p_so2 = os.path.join(ruta_fuentes, "copernicus_s5p_offl_l3_so2", "panel.zarr")
ruta_s5p_o3 = os.path.join(ruta_fuentes, "copernicus_s5p_offl_l3_o3", "panel.zarr")
ruta_era5 = os.path.join(ruta_fuentes, "ecmwf_era5_hourly", "panel.zarr")
ruta_modis_zarr = os.path.join(ruta_modis, "panel.zarr")

ruta_salida = Path("/kaggle/working/geovision-so2-p95-tiles")
ruta_salida.mkdir(parents=True, exist_ok=True)

print(f"Salida: {ruta_salida}")
```

```python
ds_s2 = xr.open_zarr(ruta_s2, chunks="auto")
ds_no2 = xr.open_zarr(ruta_s5p_no2, chunks="auto")
ds_so2 = xr.open_zarr(ruta_s5p_so2, chunks="auto")
ds_o3 = xr.open_zarr(ruta_s5p_o3, chunks="auto")
ds_era5 = xr.open_zarr(ruta_era5, chunks="auto")
ds_modis = xr.open_zarr(ruta_modis_zarr, chunks="auto")
df_scl = pd.read_csv(ruta_scl)

print("Fuentes abiertas")
```

## Bloque 2 - Preprocesamiento temporal y filtros

```python
df_scl["fecha"] = pd.to_datetime(df_scl["time_s2"].str.split("T").str[0], format="%Y%m%d")
df_scl_validas = df_scl[
    (df_scl["fecha"] >= "2021-01-01")
    & (df_scl["fecha"] <= "2024-12-31")
    & (df_scl["scl_pct"] >= 0.30)
].copy()

df_scl_validas["fecha_s2_dt"] = pd.to_datetime(
    df_scl_validas["time_s2"].str.split("_").str[0],
    format="%Y%m%dT%H%M%S",
)

print(f"Escenas S2 válidas: {len(df_scl_validas)}")
```

```python
ds_no2 = ds_no2.sel(time=slice("20210101", "20241231T235959"))
ds_so2 = ds_so2.sel(time=slice("20210101", "20241231T235959"))
ds_o3 = ds_o3.sel(time=slice("20210101", "20241231T235959"))

no2_cloud = ds_no2["data"].isel(band=2)
so2_cloud = ds_so2["data"].isel(band=1)
o3_cloud = ds_o3["data"].isel(band=1)
o3_val = ds_o3["data"].isel(band=0)

ds_no2["data"] = ds_no2["data"].where(no2_cloud < 0.7)
ds_so2["data"] = ds_so2["data"].where(so2_cloud < 0.7)
ds_o3["data"] = ds_o3["data"].where((o3_cloud < 0.7) & (o3_val > 0.0))

tiempos_era5 = pd.to_datetime(ds_era5["time"].values, format="%Y%m%dT%H")
ds_era5 = ds_era5.assign_coords(time=tiempos_era5).sel(time=slice("2021-01-01", "2024-12-31T23:59:59"))

ds_modis = ds_modis.sel(time=slice("A2021001", "A2024366"))
fechas_modis = pd.to_datetime([str(t)[1:] for t in ds_modis["time"].values], format="%Y%j")
ds_modis = ds_modis.assign_coords(time=fechas_modis)

print("Filtros temporales y nubosidad listos")
```

## Bloque 3 - Umbral SO2 p99

```python
def mapear_tiempos_s5p(ds, nombre):
    serie = ds["data"].isel(band=0).mean(dim=["x", "y"], skipna=True)
    df_temp = serie.to_dataframe(name=nombre).dropna().reset_index()
    df_temp["fecha"] = pd.to_datetime(
        df_temp["time"].astype(str).str.split("_").str[0],
        format="%Y%m%dT%H%M%S",
    )
    return df_temp[["time", "fecha", nombre]]

df_t_no2 = mapear_tiempos_s5p(ds_no2, "no2")
df_t_so2 = mapear_tiempos_s5p(ds_so2, "so2")
df_t_o3 = mapear_tiempos_s5p(ds_o3, "o3")

SO2_P75 = float(df_t_so2["so2"].quantile(0.75))
SO2_P90 = float(df_t_so2["so2"].quantile(0.90))
SO2_P95 = float(df_t_so2["so2"].quantile(0.95))
SO2_P99 = float(df_t_so2["so2"].quantile(0.99))
SO2_UMBRAL = SO2_P99

print(f"SO2 p75: {SO2_P75:.8f}")
print(f"SO2 p90: {SO2_P90:.8f}")
print(f"SO2 p95: {SO2_P95:.8f}")
print(f"SO2 p99: {SO2_P99:.8f}")
print(f"Umbral usado: SO2 >= {SO2_UMBRAL:.8f}")
```

## Bloque 4 - Funciones de extracción

```python
TILE_SIZE = 64
SCL_TILE_MIN = 0.30
N_OBJETIVO = 230
N_CANDIDATOS_MIN = 230
MAX_INTENTOS = 30000
WORKERS = 24
CHECKPOINT_FREQ = 300
OFFSET_SEED = 202405

bands_s2 = list(ds_s2.coords["band"].values)
```

```python
def extraer_tile_s2(escena, y0, x0, tile_size=64):
    return escena["data"].isel(y=slice(y0, y0 + tile_size), x=slice(x0, x0 + tile_size)).values.astype("float32")


def centroide_tile(escena, y0, x0, tile_size=64):
    y_c = y0 + tile_size // 2
    x_c = x0 + tile_size // 2
    return float(escena["y"].values[y_c]), float(escena["x"].values[x_c])


def calcular_indices_tile(tile, bands):
    idx_b4 = list(bands).index("B4")
    idx_b8 = list(bands).index("B8")
    idx_b11 = list(bands).index("B11")
    idx_scl = list(bands).index("SCL")

    red = tile[idx_b4]
    nir = tile[idx_b8]
    swir = tile[idx_b11]
    scl = tile[idx_scl]

    ndvi = np.nanmean((nir - red) / (nir + red + 1e-6))
    ndbi = np.nanmean((swir - nir) / (swir + nir + 1e-6))
    scl_pct = np.isin(scl, [4, 5, 6, 7]).mean()
    return float(ndvi), float(ndbi), float(scl_pct)


def muestrear_tile_valido(escena, bands, tile_size=64, scl_min=0.30, max_intentos=50):
    ny, nx = escena.sizes["y"], escena.sizes["x"]
    for _ in range(max_intentos):
        y0 = int(rng.integers(0, ny - tile_size))
        x0 = int(rng.integers(0, nx - tile_size))
        tile = extraer_tile_s2(escena, y0, x0, tile_size)
        ndvi, ndbi, scl_pct = calcular_indices_tile(tile, bands)
        if scl_pct >= scl_min and np.isfinite(ndvi) and np.isfinite(ndbi):
            lat, lon = centroide_tile(escena, y0, x0, tile_size)
            return {
                "tile": tile,
                "y0": y0,
                "x0": x0,
                "lat": lat,
                "lon": lon,
                "ndvi": ndvi,
                "ndbi": ndbi,
                "scl_pct": scl_pct,
            }
    return None
```

```python
def extraer_punto_s5p(ds, lat, lon, time_value, band_idx=0, ventana=1):
    ds_time = ds.sel(time=time_value)
    y_vals = ds_time["y"].values
    x_vals = ds_time["x"].values
    iy = int(np.abs(y_vals - lat).argmin())
    ix = int(np.abs(x_vals - lon).argmin())
    y0, y1 = max(0, iy - ventana), min(len(y_vals), iy + ventana + 1)
    x0, x1 = max(0, ix - ventana), min(len(x_vals), ix + ventana + 1)
    bloque = ds_time["data"].isel(band=band_idx, y=slice(y0, y1), x=slice(x0, x1)).values
    return float(np.nanmean(bloque)) if np.isfinite(bloque).any() else np.nan


def extraer_s5p_cercano_en_punto(ds, df_tiempos, lat, lon, fecha_s2, ventana_dias=1, ventana_espacial=1):
    fecha_s2 = pd.Timestamp(fecha_s2)
    delta = (df_tiempos["fecha"] - fecha_s2).abs()
    candidatos = df_tiempos[delta <= pd.Timedelta(days=ventana_dias)].copy()
    if candidatos.empty:
        return np.nan
    candidatos["delta"] = (candidatos["fecha"] - fecha_s2).abs()
    candidatos = candidatos.sort_values("delta")
    for _, fila in candidatos.iterrows():
        valor = extraer_punto_s5p(ds, lat, lon, fila["time"], band_idx=0, ventana=ventana_espacial)
        if np.isfinite(valor):
            return valor
    return np.nan


def extraer_s5p_tile(lat, lon, fecha_s2):
    no2 = extraer_s5p_cercano_en_punto(ds_no2, df_t_no2, lat, lon, fecha_s2, ventana_dias=1, ventana_espacial=1)
    so2 = extraer_s5p_cercano_en_punto(ds_so2, df_t_so2, lat, lon, fecha_s2, ventana_dias=1, ventana_espacial=1)
    o3 = extraer_s5p_cercano_en_punto(ds_o3, df_t_o3, lat, lon, fecha_s2, ventana_dias=1, ventana_espacial=1)
    return no2, so2, o3
```

```python
def extraer_modis_valor(lat, lon, fecha_s2, band_idx, ventana_espacial=2, ventana_dias=3):
    fecha_base = pd.Timestamp(fecha_s2).normalize()
    fechas_candidatas = [fecha_base + pd.Timedelta(days=d) for d in range(-ventana_dias, ventana_dias + 1)]
    fechas_candidatas = sorted(fechas_candidatas, key=lambda f: abs((f - fecha_base).days))
    for fecha in fechas_candidatas:
        if fecha < pd.Timestamp("2021-01-01") or fecha > pd.Timestamp("2024-12-31"):
            continue
        ds_time = ds_modis.sel(time=fecha)
        y_vals = ds_time["y"].values
        x_vals = ds_time["x"].values
        iy = int(np.abs(y_vals - lat).argmin())
        ix = int(np.abs(x_vals - lon).argmin())
        y0, y1 = max(0, iy - ventana_espacial), min(len(y_vals), iy + ventana_espacial + 1)
        x0, x1 = max(0, ix - ventana_espacial), min(len(x_vals), ix + ventana_espacial + 1)
        bloque = ds_time["data"].isel(band=band_idx, y=slice(y0, y1), x=slice(x0, x1)).values
        if np.isfinite(bloque).any():
            return float(np.nanmean(bloque))
    return np.nan


def extraer_modis_tile(lat, lon, fecha_s2):
    return {
        "modis_AOD_047": extraer_modis_valor(lat, lon, fecha_s2, band_idx=0),
        "modis_AOD_055": extraer_modis_valor(lat, lon, fecha_s2, band_idx=1),
        "modis_WV": extraer_modis_valor(lat, lon, fecha_s2, band_idx=2),
    }


def extraer_era5_tile(lat, lon, fecha_s2):
    fecha_hora = pd.Timestamp(fecha_s2).round("h")
    punto = ds_era5.sel(time=fecha_hora, y=lat, x=lon, method="nearest")
    valores = punto["data"].values.astype("float32")
    return {
        "era5_T2m": float(valores[0]),
        "era5_Td2m": float(valores[1]),
        "era5_u10": float(valores[2]),
        "era5_v10": float(valores[3]),
        "era5_BLH": float(valores[4]),
        "era5_RH850": float(valores[5]),
        "era5_psurf": float(valores[6]),
        "era5_precip": float(valores[7]),
    }
```

## Bloque 5 - Extracción paralela de candidatos SO2 p99

```python
def guardar_checkpoint_so2(tiles, metas, intentos_evaluados):
    hora = datetime.datetime.now().strftime("%H:%M:%S")
    tasa = len(tiles) / max(intentos_evaluados, 1)
    tqdm.write(
        f"[{hora}] Intentos={intentos_evaluados} | "
        f"válidos={len(tiles)}/{N_OBJETIVO} | "
        f"tasa={tasa:.4f}"
    )

    if len(tiles) == 0:
        return

    ruta_ckpt = ruta_salida / "checkpoints_so2_p99"
    ruta_ckpt.mkdir(parents=True, exist_ok=True)
    df_meta = pd.DataFrame(metas)
    tiles_arr = np.stack(tiles).astype("float32")
    df_meta.to_parquet(ruta_ckpt / f"meta_ckpt_{intentos_evaluados}_intentos.parquet", index=False)
    np.savez_compressed(
        ruta_ckpt / f"tiles_ckpt_{intentos_evaluados}_intentos.npz",
        data=tiles_arr,
        bands=np.array(bands_s2),
    )
```

```python
def intentar_extraccion_so2(intento):
    try:
        fila = df_scl_validas.sample(1, random_state=SEED + OFFSET_SEED + intento).iloc[0]
        time_s2 = fila["time_s2"]
        fecha_s2 = fila["fecha_s2_dt"]
        escena = ds_s2.sel(time=time_s2)

        muestra = muestrear_tile_valido(
            escena,
            bands_s2,
            tile_size=TILE_SIZE,
            scl_min=SCL_TILE_MIN,
            max_intentos=50,
        )
        if muestra is None:
            return None

        lat = muestra["lat"]
        lon = muestra["lon"]
        ndvi = muestra["ndvi"]
        ndbi = muestra["ndbi"]
        scl_pct = muestra["scl_pct"]

        no2, so2, o3 = extraer_s5p_tile(lat, lon, fecha_s2)
        if not np.isfinite(so2) or so2 < SO2_UMBRAL:
            return None

        era5 = extraer_era5_tile(lat, lon, fecha_s2)
        modis = extraer_modis_tile(lat, lon, fecha_s2)

        texto = (
            f"Zona con SO2 extremo p99 por columna satelital Sentinel-5P, "
            f"SO2={so2:.8f}, asociada a emisiones regionales o industriales."
        )

        meta = {
            "clase": "contaminacion_alta_SO2",
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
            "texto": texto,
            "umbral_so2": SO2_UMBRAL,
            "percentil_so2": 99,
            **era5,
            **modis,
        }
        return muestra["tile"], meta
    except Exception:
        return None
```

```python
print(f"Extracción SO2 p99 con {WORKERS} workers")
print(f"Objetivo final: {N_OBJETIVO} tiles")
print(f"Pool mínimo deseado: {N_CANDIDATOS_MIN} candidatos")
print(f"Checkpoint/log cada: {CHECKPOINT_FREQ} intentos")
print(f"Máximo intentos: {MAX_INTENTOS}")

tiles_so2 = []
metas_so2 = []
intentos_evaluados = 0

with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:
    futuros = {executor.submit(intentar_extraccion_so2, i): i for i in range(MAX_INTENTOS)}

    for futuro in tqdm(concurrent.futures.as_completed(futuros), total=MAX_INTENTOS, desc="Buscando SO2 p95"):
        resultado = futuro.result()
        intentos_evaluados += 1

        if resultado is not None:
            tile, meta = resultado
            tiles_so2.append(tile)
            metas_so2.append(meta)

            tqdm.write(
                f"Candidato válido {len(tiles_so2)}/{N_OBJETIVO} | "
                f"intento={intentos_evaluados} | "
                f"SO2={meta['so2']:.8f} | "
                f"NDVI={meta['ndvi']:.3f} | "
                f"NDBI={meta['ndbi']:.3f}"
            )

            if len(tiles_so2) >= N_CANDIDATOS_MIN:
                tqdm.write(f"Meta alcanzada: {len(tiles_so2)} candidatos SO2 p99")
                guardar_checkpoint_so2(tiles_so2, metas_so2, intentos_evaluados)
                for f in futuros:
                    f.cancel()
                break

        if intentos_evaluados % CHECKPOINT_FREQ == 0:
            guardar_checkpoint_so2(tiles_so2, metas_so2, intentos_evaluados)

print(f"Intentos evaluados: {intentos_evaluados}")
print(f"Candidatos encontrados: {len(tiles_so2)}")
```

## Bloque 6 - Selección final de 230 tiles SO2

```python
def seleccionar_diverso_por_fecha_y_espacio(df, n=230, min_dist_grados=0.003):
    df = df.sort_values("so2", ascending=False).reset_index(drop=True)
    seleccion = []
    fechas_usadas = {}

    for idx, row in df.iterrows():
        fecha = pd.Timestamp(row["fecha_s2"]).date()
        if fechas_usadas.get(fecha, 0) >= 8:
            continue

        if seleccion:
            prev = df.loc[seleccion, ["lat", "lon"]].values
            dist = np.sqrt(((prev - np.array([row["lat"], row["lon"]])) ** 2).sum(axis=1))
            if (dist < min_dist_grados).sum() >= 3:
                continue

        seleccion.append(idx)
        fechas_usadas[fecha] = fechas_usadas.get(fecha, 0) + 1
        if len(seleccion) >= n:
            break

    if len(seleccion) < n:
        faltan = n - len(seleccion)
        restantes = [i for i in df.index if i not in seleccion]
        seleccion.extend(restantes[:faltan])

    return df.loc[seleccion].reset_index(drop=True), seleccion


df_candidatos_so2 = pd.DataFrame(metas_so2)
assert len(df_candidatos_so2) >= N_OBJETIVO, "No hay suficientes candidatos SO2 p95"

df_final_so2, idx_sel = seleccionar_diverso_por_fecha_y_espacio(df_candidatos_so2, n=N_OBJETIVO)
tiles_final_so2 = [tiles_so2[i] for i in idx_sel]

print(df_final_so2[["so2", "ndvi", "ndbi", "scl_pct"]].describe().round(6))
print(f"Tiles finales: {len(tiles_final_so2)}")
```

```python
tiles_arr = np.stack(tiles_final_so2).astype("float32")
df_final_so2.to_parquet(ruta_salida / "tiles_meta_so2_p99.parquet", index=False)
np.savez_compressed(
    ruta_salida / "tiles_train_so2_p99.npz",
    data=tiles_arr,
    bands=np.array(bands_s2),
)

print(f"Guardado: {ruta_salida / 'tiles_meta_so2_p99.parquet'}")
print(f"Guardado: {ruta_salida / 'tiles_train_so2_p99.npz'}")
```

## Bloque 7 - Diagnóstico rápido SO2 p99

```python
print("Resumen SO2 p99 final")
print(df_final_so2[["so2", "no2", "o3", "ndvi", "ndbi", "scl_pct", "modis_AOD_047", "modis_WV", "era5_BLH", "era5_RH850"]].describe().round(6))
```

```python
try:
    import matplotlib.pyplot as plt
    import seaborn as sns

    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    for ax, col in zip(axes, ["so2", "ndvi", "ndbi"]):
        sns.histplot(df_final_so2[col], kde=True, ax=ax)
        ax.set_title(col)
    plt.tight_layout()
    plt.savefig(ruta_salida / "diagnostico_so2_p99_hist.png", dpi=160, bbox_inches="tight")
    plt.show()
except Exception as e:
    print(f"No se pudieron graficar histogramas: {e}")
```

## Bloque 8 - Crear Kaggle Dataset por código

```python
KAGGLE_USERNAME = os.environ.get("KAGGLE_USERNAME", "edwardsx")
DATASET_SLUG = "geovision-so2-p99-tiles"
DATASET_ID = f"{KAGGLE_USERNAME}/{DATASET_SLUG}"

metadata = {
    "title": "GeoVision Cali - SO2 p99 Tiles",
    "id": DATASET_ID,
    "licenses": [{"name": "CC0-1.0"}],
    "subtitle": "Clase SO2 regenerada con pseudo-label fuerte p99",
    "description": "Tiles Sentinel-2 64x64 para contaminacion_alta_SO2 regenerados con SO2 >= p99 desde Sentinel-5P, incluyendo variables ERA5 y MODIS auxiliares.",
    "keywords": ["remote sensing", "sentinel-2", "sentinel-5p", "so2", "clip", "cali"],
}

with open(ruta_salida / "dataset-metadata.json", "w", encoding="utf-8") as f:
    json.dump(metadata, f, ensure_ascii=False, indent=2)

print(f"Metadata lista: {DATASET_ID}")
```

```python
def run_kaggle_cmd(cmd):
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.stdout:
        print("STDOUT:", proc.stdout.strip())
    if proc.stderr:
        print("STDERR:", proc.stderr.strip())
    return proc

cmd_create = ["kaggle", "datasets", "create", "-p", str(ruta_salida), "--dir-mode", "zip", "--public"]
proc_create = run_kaggle_cmd(cmd_create)

salida = (proc_create.stdout + proc_create.stderr).lower()
if proc_create.returncode != 0 and ("already exists" in salida or "409" in salida):
    cmd_version = [
        "kaggle", "datasets", "version",
        "-p", str(ruta_salida),
        "-m", "Regenera SO2 con p99",
        "--dir-mode", "zip",
    ]
    run_kaggle_cmd(cmd_version)
elif proc_create.returncode != 0:
    raise RuntimeError("Falló la creación del dataset SO2 p95")

print(f"Dataset: https://www.kaggle.com/datasets/{DATASET_ID}")
```
