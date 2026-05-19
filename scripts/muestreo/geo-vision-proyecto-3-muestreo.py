# ---
# jupyter:
#   jupytext:
#     formats: py:percent,ipynb
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.2
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # GeoVision-CLIP — Muestreo + contexto físico (Situación 2)
#
# Si `tiles_train.npz` ya existe en `edwardsx/geovision-tiles-sit2`, solo se recalcula contexto
# ERA5 + MODIS v2 sobre la meta existente. Si no, se ejecuta el muestreo completo (5 clases × 1000 tiles)
# y luego el contexto.

# %%
# !pip install zarr tqdm -q

# %%
from __future__ import annotations
import json
import time
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import xarray as xr
from tqdm.auto import tqdm

try:
    import torch
except ImportError:
    torch = None

SEED = 42
TILE_PX = 64
N_BANDAS_S2 = 13
HALF = TILE_PX // 2
SCL_THRESHOLD = 0.3
SCL_UMBRAL_ESCENA = 0.3
VENTANA_S2_DIAS = 5
NDVI_URBANO_MAX = 0.30
RADIO_DAGMA_M = 1000
N_POR_CLASE = 1000
BATCH_SCL = 5

BASE_PATH = Path("/kaggle/input/datasets/juanjoseorozcolopez/geovision-fuentes")
MODIS_PATH = Path("/kaggle/input/datasets/edwardsx/modis-v2-panel")
TILES_PATH = Path("/kaggle/input/datasets/edwardsx/geovision-tiles-sit2")
OUT_DIR = Path("/kaggle/working")
CKPT_DIR = OUT_DIR / "checkpoints"
CKPT_DIR.mkdir(parents=True, exist_ok=True)

CLASES = [
    "contaminacion_alta_NO2",
    "contaminacion_alta_SO2",
    "ozono_anomalo",
    "vegetacion_densa",
    "suelo_urbano",
]
GUIADAS = [
    ("contaminacion_alta_NO2", "tropospheric_NO2_column_number_density", "NO2", "no2"),
    ("contaminacion_alta_SO2", "SO2_column_number_density", "SO2", "so2"),
    ("ozono_anomalo", "O3_column_number_density", "O3", "o3"),
]
rng = np.random.default_rng(SEED)

TEXTOS = {
    "contaminacion_alta_NO2": lambda t: f"Zona urbana con NO2 alto ({t.no2:.2e} mol/m2), trafico vehicular intenso.",
    "contaminacion_alta_SO2": lambda t: f"Pluma industrial con SO2 elevado ({t.so2:.2e} mol/m2), corredor Yumbo-Acopi.",
    "ozono_anomalo":          lambda t: f"Anomalia de ozono ({t.o3:.2e} mol/m2), fotoquimica activa.",
    "vegetacion_densa":       lambda t: f"Vegetacion densa, NDVI={t.ndvi:.2f}, cana de azucar o bosque.",
    "suelo_urbano":           lambda t: f"Zona urbana construida, NDVI={t.ndvi:.2f}, alta densidad edificada.",
}

# %% [markdown]
# ## 1. Abrir paneles satelitales

# %%
t0 = time.time()
s2    = xr.open_zarr(BASE_PATH / "copernicus_s2_sr_harmonized" / "panel.zarr", consolidated=True)
no2   = xr.open_zarr(BASE_PATH / "copernicus_s5p_offl_l3_no2"  / "panel.zarr", consolidated=True)
so2   = xr.open_zarr(BASE_PATH / "copernicus_s5p_offl_l3_so2"  / "panel.zarr", consolidated=True)
o3    = xr.open_zarr(BASE_PATH / "copernicus_s5p_offl_l3_o3"   / "panel.zarr", consolidated=True)
era5  = xr.open_zarr(BASE_PATH / "ecmwf_era5_hourly"           / "panel.zarr", consolidated=True)
modis = xr.open_zarr(MODIS_PATH / "panel.zarr")

dagma_df   = pd.read_parquet(BASE_PATH / "dagma" / "dagma_cvc_horario_raw.parquet")
estaciones = pd.read_csv(BASE_PATH / "dagma" / "estaciones_metadata.csv")

bands_s2 = s2["band"].values.tolist()
y_coords = s2["y"].values
x_coords = s2["x"].values

print(f"Paneles en {time.time()-t0:.1f}s")
print(f"  S2: {dict(s2.sizes)}  | NO2: {dict(no2.sizes)}  | SO2: {dict(so2.sizes)}  | O3: {dict(o3.sizes)}")
print(f"  ERA5: {dict(era5.sizes)}  | MODIS v2: {dict(modis.sizes)}")
print(f"  DAGMA: {len(dagma_df):,} filas, {len(estaciones)} estaciones")

# %% [markdown]
# ## 2. Parsear timestamps de cada panel

# %%
def parse_time(s):
    s = str(s)
    if len(s) == 8 and s[0] in "ATMP" and s[1:].isdigit():
        return pd.Timestamp(year=int(s[1:5]), month=1, day=1) + pd.Timedelta(days=int(s[5:8]) - 1)
    if "_" in s:
        s = s.split("_")[0]
    if len(s) >= 9 and s[8:9] == "T":
        if len(s) == 11:
            return pd.to_datetime(s + "0000", format="%Y%m%dT%H%M%S")
        return pd.to_datetime(s[:15], format="%Y%m%dT%H%M%S")
    return pd.to_datetime(s)


t0 = time.time()
times = {
    k: pd.DatetimeIndex([parse_time(t) for t in ds["time"].values])
    for k, ds in [("s2", s2), ("no2", no2), ("so2", so2), ("o3", o3), ("era5", era5), ("modis", modis)]
}
print(f"Parseados en {time.time()-t0:.1f}s")
for k, v in times.items():
    print(f"  {k:<6}: {v[0]} a {v[-1]}  ({len(v):,})")

# %% [markdown]
# ## 3. Cargar tiles existentes (cache) o disparar muestreo

# %%
TILES_NPZ_IN  = TILES_PATH / "tiles_train.npz"
TILES_META_IN = TILES_PATH / "tiles_meta.parquet"

if TILES_NPZ_IN.exists() and TILES_META_IN.exists():
    loaded = np.load(TILES_NPZ_IN)
    tiles_arr = loaded["data"]
    meta = pd.read_parquet(TILES_META_IN)
    CARGADOS = True
    print(f"Tiles cargados desde {TILES_PATH.name}: {tiles_arr.shape}")
    print(meta["clase"].value_counts())
else:
    CARGADOS = False
    print("Tiles no encontrados, se ejecutará muestreo completo abajo")

# %% [markdown]
# ## 4. Muestreo completo (solo si CARGADOS=False)

# %% [markdown]
# ### 4.1 Pre-filtrado SCL por escena con GPU

# %%
if not CARGADOS:
    out_scl = OUT_DIR / "scl_por_escena.csv"
    inp_scl = BASE_PATH / "scl_por_escena.csv"

    if out_scl.exists():
        scl_pct = pd.read_csv(out_scl)["scl_pct"].values.astype("float32")
    elif inp_scl.exists():
        scl_pct = pd.read_csv(inp_scl)["scl_pct"].values.astype("float32")
    else:
        assert torch.cuda.is_available(), "Activar GPU T4"
        device = "cuda"
        scl_da = s2["data"].sel(band="SCL")
        n_t = s2.sizes["time"]
        scl_pct = np.zeros(n_t, dtype="float32")
        for ti in tqdm(range(0, n_t, BATCH_SCL), desc="SCL (GPU)"):
            block = scl_da.isel(time=slice(ti, ti + BATCH_SCL)).values
            t = torch.from_numpy(block).to(device)
            valid  = ((t >= 4) & (t <= 7)).float()
            finite = torch.isfinite(t).float()
            pct = (valid.sum(dim=[-1, -2]) / finite.sum(dim=[-1, -2]).clamp(min=1)).cpu().numpy()
            scl_pct[ti:ti + len(pct)] = pct
        pd.DataFrame({
            "time_idx": np.arange(n_t),
            "time_s2":  [str(t) for t in s2["time"].values],
            "scl_pct":  scl_pct,
        }).to_csv(out_scl, index=False)

    ESCENAS_LIMPIAS = np.where(scl_pct > SCL_UMBRAL_ESCENA)[0]
    print(f"Escenas limpias (SCL > {SCL_UMBRAL_ESCENA}): {len(ESCENAS_LIMPIAS)}/{len(scl_pct)}")

# %% [markdown]
# ### 4.2 Percentiles S5P (incluye p95 para O3)

# %%
if not CARGADOS:
    def _perc(panel, banda, n=500):
        idx = np.sort(rng.choice(panel.sizes["time"], size=min(n, panel.sizes["time"]), replace=False))
        data = panel["data"].sel(band=banda).isel(time=idx).values.ravel()
        data = data[np.isfinite(data)]
        data = data[np.abs(data) > 1e-12] if banda != "O3_column_number_density" else data[data > 0]
        return {p: float(np.percentile(data, p)) for p in [10, 25, 50, 75, 90, 95, 99]} | {"n": int(data.size)}

    perc = {
        "NO2": _perc(no2, "tropospheric_NO2_column_number_density"),
        "SO2": _perc(so2, "SO2_column_number_density"),
        "O3":  _perc(o3,  "O3_column_number_density"),
    }
    for g, p in perc.items():
        print(f"  {g}: p50={p[50]:.2e}  p90={p[90]:.2e}  p95={p[95]:.2e}  p99={p[99]:.2e}  (n={p['n']:,})")

# %% [markdown]
# ### 4.3 Helpers de extracción de tiles

# %%
if not CARGADOS:
    @dataclass
    class Tile:
        t_idx: int
        time_s2: str
        y_idx: int
        x_idx: int
        lat: float
        lon: float
        clase: Optional[str] = None
        no2: float = np.nan
        so2: float = np.nan
        o3: float = np.nan
        ndvi: float = np.nan
        ndbi: float = np.nan
        scl_pct: float = np.nan

    def extraer(t_idx, y_idx, x_idx):
        return s2["data"].isel(
            time=t_idx,
            y=slice(y_idx - HALF, y_idx + HALF),
            x=slice(x_idx - HALF, x_idx + HALF),
        ).values

    def ndvi_fn(tile):
        nir = tile[bands_s2.index("B8")].astype("float64")
        red = tile[bands_s2.index("B4")].astype("float64")
        d = np.where((nir + red) == 0, np.nan, nir + red)
        return float(np.nanmean((nir - red) / d))

    def ndbi_fn(tile):
        swir = tile[bands_s2.index("B11")].astype("float64")
        nir  = tile[bands_s2.index("B8")].astype("float64")
        d = np.where((swir + nir) == 0, np.nan, swir + nir)
        return float(np.nanmean((swir - nir) / d))

    def scl_tile(tile):
        return float(np.isin(tile[bands_s2.index("SCL")], [4, 5, 6, 7]).mean())

    PANELES = {"NO2": no2, "SO2": so2, "O3": o3}

# %% [markdown]
# ### 4.4 Muestreo guiado S5P (NO2, SO2, O3)

# %%
if not CARGADOS:
    aceptados = {}
    for clase, banda, key_p, key_t in GUIADAS:
        panel = PANELES[key_p]
        arr = panel["data"].sel(band=banda).values
        umbral = perc[key_p][95 if key_p == "O3" else 90]
        t_hot, y_hot, x_hot = np.where(np.isfinite(arr) & (arr > umbral))
        perm = rng.permutation(len(t_hot))
        print(f"  [{clase}] {len(t_hot):,} hot pixels, umbral={umbral:.2e}")

        aceptados[clase] = []
        max_int = N_POR_CLASE * 60
        rj_ns = rj_sc = rj_bd = 0
        pbar = tqdm(total=N_POR_CLASE, desc=f"  {clase}", unit="tile")
        t0 = time.time()

        for k in perm:
            if len(aceptados[clase]) >= N_POR_CLASE:
                break
            if len(aceptados[clase]) + rj_ns + rj_sc + rj_bd >= max_int:
                break

            tp = int(t_hot[k])
            lat_p = float(panel["y"].values[int(y_hot[k])])
            lon_p = float(panel["x"].values[int(x_hot[k])])

            dt = np.abs((times["s2"] - times[key_t][tp]).total_seconds().values)
            cands = np.where(dt < VENTANA_S2_DIAS * 86400)[0]
            cands = np.intersect1d(cands, ESCENAS_LIMPIAS, assume_unique=True)
            cands = cands[np.argsort(dt[cands])] if len(cands) else np.array([], dtype=int)
            if len(cands) == 0:
                rj_ns += 1
                continue

            lat = lat_p + float(rng.uniform(-0.0018, 0.0018))
            lon = lon_p + float(rng.uniform(-0.0018, 0.0018))
            y = int(np.argmin(np.abs(y_coords - lat)))
            x = int(np.argmin(np.abs(x_coords - lon)))
            if not (HALF <= y < s2.sizes["y"] - HALF and HALF <= x < s2.sizes["x"] - HALF):
                rj_bd += 1
                continue

            ok = False
            for ts in cands[:5]:
                tile = extraer(int(ts), y, x)
                if tile.shape != (N_BANDAS_S2, TILE_PX, TILE_PX):
                    continue
                if scl_tile(tile) < SCL_THRESHOLD:
                    continue
                t_obj = Tile(
                    t_idx=int(ts),
                    time_s2=str(s2["time"].values[int(ts)]),
                    y_idx=y, x_idx=x,
                    lat=float(y_coords[y]), lon=float(x_coords[x]),
                    clase=clase,
                    scl_pct=scl_tile(tile),
                    ndvi=ndvi_fn(tile),
                    ndbi=ndbi_fn(tile),
                )
                val = float(arr[tp, int(y_hot[k]), int(x_hot[k])])
                if   key_p == "NO2": t_obj.no2 = val
                elif key_p == "SO2": t_obj.so2 = val
                else:                t_obj.o3  = val
                aceptados[clase].append((t_obj, tile))
                ok = True
                pbar.update(1)
                break
            if not ok:
                rj_sc += 1
        pbar.close()
        print(f"  [{clase}] {len(aceptados[clase])}/{N_POR_CLASE} en {time.time()-t0:.1f}s "
              f"(rj_s2={rj_ns} rj_scl={rj_sc} rj_borde={rj_bd})")

# %% [markdown]
# ### 4.5 Muestreo: vegetacion_densa (NDVI > 0.6)

# %%
if not CARGADOS:
    clase = "vegetacion_densa"
    aceptados[clase] = []
    max_int = N_POR_CLASE * 80
    rj_sc = rj_cl = 0
    pbar = tqdm(total=N_POR_CLASE, desc=f"  {clase}", unit="tile")
    t0 = time.time()
    while len(aceptados[clase]) < N_POR_CLASE and len(aceptados[clase]) + rj_sc + rj_cl < max_int:
        t = int(rng.choice(ESCENAS_LIMPIAS))
        y = int(rng.integers(HALF, s2.sizes["y"] - HALF))
        x = int(rng.integers(HALF, s2.sizes["x"] - HALF))
        tile = extraer(t, y, x)
        if tile.shape != (N_BANDAS_S2, TILE_PX, TILE_PX):
            continue
        if scl_tile(tile) < SCL_THRESHOLD:
            rj_sc += 1
            continue
        nd = ndvi_fn(tile)
        nb = ndbi_fn(tile)
        if nd > 0.6:
            aceptados[clase].append((Tile(
                t_idx=t, time_s2=str(s2["time"].values[t]), y_idx=y, x_idx=x,
                lat=float(y_coords[y]), lon=float(x_coords[x]),
                clase=clase, scl_pct=scl_tile(tile), ndvi=nd, ndbi=nb), tile))
            pbar.update(1)
        else:
            rj_cl += 1
    pbar.close()
    print(f"  [{clase}] {len(aceptados[clase])}/{N_POR_CLASE} en {time.time()-t0:.1f}s "
          f"(rj_scl={rj_sc} rj_clase={rj_cl})")

# %% [markdown]
# ### 4.6 Muestreo: suelo_urbano (guiado DAGMA, NDVI < 0.30)

# %%
if not CARGADOS:
    clase = "suelo_urbano"
    RPX = int(RADIO_DAGMA_M / 10)
    dagma_yx = [
        (int(np.argmin(np.abs(y_coords - row["latitud"]))),
         int(np.argmin(np.abs(x_coords - row["longitud"]))))
        for _, row in estaciones.iterrows()
    ]
    aceptados[clase] = []
    max_int = N_POR_CLASE * 40
    rj_sc = rj_cl = rj_bd = 0
    pbar = tqdm(total=N_POR_CLASE, desc=f"  {clase}", unit="tile")
    t0 = time.time()
    while len(aceptados[clase]) < N_POR_CLASE and len(aceptados[clase]) + rj_sc + rj_cl + rj_bd < max_int:
        ey, ex_ = dagma_yx[int(rng.integers(0, len(dagma_yx)))]
        y = ey + int(rng.integers(-RPX, RPX + 1))
        x = ex_ + int(rng.integers(-RPX, RPX + 1))
        if not (HALF <= y < s2.sizes["y"] - HALF and HALF <= x < s2.sizes["x"] - HALF):
            rj_bd += 1
            continue
        t = int(rng.choice(ESCENAS_LIMPIAS))
        tile = extraer(t, y, x)
        if tile.shape != (N_BANDAS_S2, TILE_PX, TILE_PX):
            continue
        if scl_tile(tile) < SCL_THRESHOLD:
            rj_sc += 1
            continue
        nd = ndvi_fn(tile)
        if nd < NDVI_URBANO_MAX:
            aceptados[clase].append((Tile(
                t_idx=t, time_s2=str(s2["time"].values[t]), y_idx=y, x_idx=x,
                lat=float(y_coords[y]), lon=float(x_coords[x]),
                clase=clase, scl_pct=scl_tile(tile), ndvi=nd, ndbi=ndbi_fn(tile)), tile))
            pbar.update(1)
        else:
            rj_cl += 1
    pbar.close()
    print(f"  [{clase}] {len(aceptados[clase])}/{N_POR_CLASE} en {time.time()-t0:.1f}s "
          f"(rj_scl={rj_sc} rj_clase={rj_cl} rj_borde={rj_bd})")

# %% [markdown]
# ### 4.7 Consolidar tiles muestreados en arrays

# %%
if not CARGADOS:
    total = sum(len(v) for v in aceptados.values())
    print(f"Total muestreado: {total}/{N_POR_CLASE * len(CLASES)}")
    for c, lst in aceptados.items():
        print(f"  {c}: {len(lst)}")
    todos = [(c, t, tile) for c, lst in aceptados.items() for t, tile in lst]
    tiles_arr = np.stack([tile for _, _, tile in todos])
    meta = pd.DataFrame([{
        "clase":   c,
        "time_s2": t.time_s2,
        "lat":     t.lat,
        "lon":     t.lon,
        "ndvi":    t.ndvi,
        "ndbi":    t.ndbi,
        "scl_pct": t.scl_pct,
        "no2":     t.no2,
        "so2":     t.so2,
        "o3":      t.o3,
        "texto":   TEXTOS[c](t),
    } for c, t, _ in todos])
    print(f"tiles_arr: {tiles_arr.shape} | meta: {meta.shape}")

# %% [markdown]
# ## 5. Recalcular contexto físico ERA5 + MODIS v2 (siempre)
#
# Si la meta cargada del cache ya tiene columnas `era5_*` o `modis_*` (de un run anterior),
# se eliminan antes de re-calcular con MODIS v2.

# %%
ERA5_BANDS = {
    "temperature_2m":           "T2m",
    "dewpoint_temperature_2m":  "Td2m",
    "u_component_of_wind_10m":  "u10",
    "v_component_of_wind_10m":  "v10",
    "boundary_layer_height":    "BLH",
    "relative_humidity_850hPa": "RH850",
    "surface_pressure":         "psurf",
    "total_precipitation":      "precip",
}
MODIS_BANDS = {
    "Optical_Depth_047": "AOD_047",
    "Optical_Depth_055": "AOD_055",
    "Column_WV":         "WV",
}


def contexto(panel, kt, lat, lon, t_dt, bm, pref):
    idx = int(np.abs((times[kt] - t_dt).total_seconds().values).argmin())
    disp = panel["band"].values.tolist()
    out = {}
    for src, suf in bm.items():
        col = f"{pref}_{suf}"
        if src not in disp:
            out[col] = np.nan
            continue
        try:
            v = float(panel["data"].sel(band=src).isel(time=idx)
                      .sel(y=lat, x=lon, method="nearest").values)
            out[col] = v if np.isfinite(v) else np.nan
        except Exception:
            out[col] = np.nan
    return out


ctx_viejas = [c for c in meta.columns if c.startswith("era5_") or c.startswith("modis_")]
if ctx_viejas:
    print(f"Eliminando {len(ctx_viejas)} columnas viejas de contexto: {ctx_viejas}")
    meta = meta.drop(columns=ctx_viejas)

t0 = time.time()
records = []
for _, row in tqdm(meta.iterrows(), total=len(meta), desc="Contexto"):
    t_dt = parse_time(row["time_s2"])
    rec = (
        contexto(era5,  "era5",  row["lat"], row["lon"], t_dt, ERA5_BANDS,  "era5")
        | contexto(modis, "modis", row["lat"], row["lon"], t_dt, MODIS_BANDS, "modis")
    )
    records.append(rec)

df_ctx = pd.DataFrame(records)
meta = pd.concat([meta.reset_index(drop=True), df_ctx.reset_index(drop=True)], axis=1)
print(f"Contexto en {time.time()-t0:.1f}s")
for c in df_ctx.columns:
    print(f"  {c:<14}: notna={df_ctx[c].notna().sum()}/{len(df_ctx)}")

# %% [markdown]
# ## 6. Guardar tiles + meta en /kaggle/working/

# %%
OUT_DIR.mkdir(parents=True, exist_ok=True)
np.savez_compressed(OUT_DIR / "tiles_train.npz", data=tiles_arr, bands=np.array(bands_s2))
meta.to_parquet(OUT_DIR / "tiles_meta.parquet")

for f in ["tiles_train.npz", "tiles_meta.parquet", "scl_por_escena.csv"]:
    p = OUT_DIR / f
    if p.exists():
        print(f"  {f}: {p.stat().st_size / 1024**2:.1f} MB")

# %% [markdown]
# ## 7. Auditoría: diversidad temporal, NDVI/NDBI y contexto físico

# %%
meta_chk = pd.read_parquet(OUT_DIR / "tiles_meta.parquet")
meta_chk["fecha"] = pd.to_datetime(meta_chk["time_s2"].str[:8], format="%Y%m%d")

print("=" * 60); print("Diversidad temporal por clase")
print("=" * 60)
for c, g in meta_chk.groupby("clase"):
    vc = g["fecha"].value_counts()
    top5 = vc.head(5).sum()
    print(f"  {c}: {g['fecha'].nunique():>3} fechas | max={vc.max():>3} tiles/fecha | top5={100*top5/len(g):.0f}%")

print("=" * 60); print("NDVI / NDBI por clase")
print("=" * 60)
for c, g in meta_chk.groupby("clase"):
    print(f"  {c}: NDVI={g['ndvi'].mean():+.2f}+-{g['ndvi'].std():.2f}  "
          f"NDBI={g['ndbi'].mean():+.2f}+-{g['ndbi'].std():.2f}  "
          f"SCL={g['scl_pct'].mean():.2f}")

print("=" * 60); print("Contexto físico (cobertura no-NaN)")
print("=" * 60)
for col in ["era5_T2m", "era5_BLH", "era5_RH850", "modis_AOD_055", "modis_AOD_047", "modis_WV"]:
    if col in meta_chk:
        s = meta_chk[col]
        if s.notna().sum() == 0:
            print(f"  {col}: 0/{len(s)}  (todo NaN)")
        else:
            print(f"  {col}: notna={s.notna().sum()}/{len(s)}  "
                  f"mean={s.mean():.3g}  rango=[{s.min():.3g}, {s.max():.3g}]")

# %% [markdown]
# ## 8. Empaquetar y subir nueva versión del dataset Kaggle
#
# Por defecto se prepara la carpeta pero NO se sube: descomentar la última línea.

# %%
UP = OUT_DIR / "upload_tiles"
UP.mkdir(exist_ok=True)

# Preservar TODOS los archivos: si se regeneró en /kaggle/working/ lo tomamos de ahí,
# si no existe pero está en el dataset montado, lo copiamos desde TILES_PATH para no perderlo
# al subir nueva versión (Kaggle reemplaza, no agrega).
for f in ["tiles_train.npz", "tiles_meta.parquet", "scl_por_escena.csv"]:
    src_working = OUT_DIR / f
    src_dataset = TILES_PATH / f
    if src_working.exists():
        shutil.copy(src_working, UP / f)
        print(f"  {f} ← /kaggle/working/")
    elif src_dataset.exists():
        shutil.copy(src_dataset, UP / f)
        print(f"  {f} ← dataset montado (preservado)")
    else:
        print(f"  ⚠ {f} no encontrado en ninguna ruta")

(UP / "dataset-metadata.json").write_text(json.dumps({
    "title":    "GeoVision Tiles Sit 2",
    "id":       "edwardsx/geovision-tiles-sit2",
    "licenses": [{"name": "CC-BY-SA-4.0"}],
}, indent=2))

print(f"\nListo en {UP}: {[p.name for p in UP.iterdir()]}")
# !kaggle datasets version -p /kaggle/working/upload_tiles -m "MODIS v2 contexto recalculado"
