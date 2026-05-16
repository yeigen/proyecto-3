"""
Muestreo estratificado para Situacion 2 - GeoVision-CLIP Cali.

Modo target-driven: para cada clase, propone candidatos hasta llenar la cuota
o agotar el budget de intentos. Garantiza balance entre las 5 clases.

Uso en Kaggle (notebook https://www.kaggle.com/code/edwardsx/geovision-proyecto-3
con dataset juanjoseorozcolopez/geovision-fuentes montado):

    from scripts.01_muestreo_kaggle import run

    # Test rapido (25 tiles, dry-run)
    aceptados, perc, stats = run(n_tiles=25, dry_run=True)

    # Generacion full (5000 tiles, escribe en /kaggle/working/)
    aceptados, perc, stats = run(n_tiles=5000, dry_run=False)

Outputs en /kaggle/working/:
    - tiles_train.npz       (data: float32 (N, 13, 64, 64), bands: array)
    - tiles_meta.parquet    (clase, time_s2, lat, lon, NDVI, NDBI, S5P, texto)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

# ---------------------------------------------------------------------------
# Constantes

SEED = 42
N_BANDAS_S2 = 13
TILE_PX = 64
SCL_THRESHOLD = 0.5  # fraccion minima de pixeles SCL en {veg, suelo, agua, unclass}

BASE_PATH = Path("/kaggle/input/datasets/juanjoseorozcolopez/geovision-fuentes")
OUT_DIR = Path("/kaggle/working")

CLASES = [
    "contaminacion_alta_NO2",
    "contaminacion_alta_SO2",
    "ozono_anomalo",
    "vegetacion_densa",
    "suelo_urbano",
]

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger("muestreo")


# ---------------------------------------------------------------------------
# Apertura de paneles


def abrir_panel(nombre: str) -> xr.Dataset:
    return xr.open_zarr(BASE_PATH / nombre / "panel.zarr", consolidated=True)


def cargar_dagma() -> tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.read_parquet(BASE_PATH / "dagma" / "dagma_cvc_horario_raw.parquet")
    est = pd.read_csv(BASE_PATH / "dagma" / "estaciones_metadata.csv")
    return df, est


# ---------------------------------------------------------------------------
# Parseo de tiempos (system_index de GEE)


def parse_kaggle_time(s) -> pd.Timestamp:
    """
    Parsea formatos:
      '20210103T152641_20210103T153117_T18NUJ'   (S2)
      '20201231T234906_20210102T163556'          (S5P)
      '20210101T00'                              (ERA5)
      '2021-01-01T00:00:00'                      (ISO)
    """
    s = str(s)
    if "_" in s:
        s = s.split("_")[0]
    if len(s) >= 9 and s[8:9] == "T":
        if len(s) == 11:
            return pd.to_datetime(s + "0000", format="%Y%m%dT%H%M%S")
        if len(s) >= 15:
            return pd.to_datetime(s[:15], format="%Y%m%dT%H%M%S")
    return pd.to_datetime(s)


_TIMES_CACHE: dict[str, pd.DatetimeIndex] = {}


def times_parseados(panel, name: str) -> pd.DatetimeIndex:
    if name not in _TIMES_CACHE:
        _TIMES_CACHE[name] = pd.DatetimeIndex(
            [parse_kaggle_time(t) for t in panel["time"].values])
    return _TIMES_CACHE[name]


def alinear_t(t_s2: str, panel, name: str) -> int:
    t_s2_ts = parse_kaggle_time(t_s2)
    ts = times_parseados(panel, name)
    return int(np.abs((ts - t_s2_ts).total_seconds().values).argmin())


# ---------------------------------------------------------------------------
# Percentiles S5P (sobre pixeles, no sobre promedios por timestamp)


def calcular_percentiles_s5p(no2, so2, o3, n_sample: int = 500,
                              rng: np.random.Generator | None = None) -> dict:
    rng = rng or np.random.default_rng(SEED)
    out = {}
    for nombre, ds, banda in [
        ("NO2", no2, "tropospheric_NO2_column_number_density"),
        ("SO2", so2, "SO2_column_number_density"),
        ("O3",  o3,  "O3_column_number_density"),
    ]:
        n_t = ds.sizes["time"]
        idx = np.sort(rng.choice(n_t, size=min(n_sample, n_t), replace=False))
        data = ds["data"].sel(band=banda).isel(time=idx).values.ravel()
        data = data[np.isfinite(data)]
        if nombre != "O3":
            data = data[np.abs(data) > 1e-12]
        else:
            data = data[data > 0]  # fillvalue=0 en O3
        out[nombre] = {
            "p10": float(np.percentile(data, 10)),
            "p25": float(np.percentile(data, 25)),
            "p50": float(np.percentile(data, 50)),
            "p75": float(np.percentile(data, 75)),
            "p90": float(np.percentile(data, 90)),
            "p99": float(np.percentile(data, 99)),
            "n_validos": int(data.size),
        }
    return out


# ---------------------------------------------------------------------------
# Tile candidato y extraccion


@dataclass
class TileCand:
    time_idx_s2: int
    time_s2: str
    y_idx: int
    x_idx: int
    lat: float
    lon: float
    clase: str | None = None
    no2: float = np.nan
    so2: float = np.nan
    o3: float = np.nan
    ndvi: float = np.nan
    ndbi: float = np.nan
    scl_pct: float = np.nan


def extraer_tile(s2, cand: TileCand) -> np.ndarray:
    half = TILE_PX // 2
    return s2["data"].isel(
        time=cand.time_idx_s2,
        y=slice(cand.y_idx - half, cand.y_idx + half),
        x=slice(cand.x_idx - half, cand.x_idx + half),
    ).values


def valor_s5p(panel, lat: float, lon: float, banda: str, t_idx: int) -> float:
    arr = panel["data"].sel(band=banda).isel(time=t_idx).sel(
        y=lat, x=lon, method="nearest").values
    return float(arr) if np.isfinite(arr) else np.nan


def calc_ndvi(tile: np.ndarray, bands: list[str]) -> float:
    nir = tile[bands.index("B8")].astype("float64")
    red = tile[bands.index("B4")].astype("float64")
    d = np.where((nir + red) == 0, np.nan, nir + red)
    return float(np.nanmean((nir - red) / d))


def calc_ndbi(tile: np.ndarray, bands: list[str]) -> float:
    swir = tile[bands.index("B11")].astype("float64")
    nir = tile[bands.index("B8")].astype("float64")
    d = np.where((swir + nir) == 0, np.nan, swir + nir)
    return float(np.nanmean((swir - nir) / d))


def scl_valido(tile: np.ndarray, bands: list[str]) -> float:
    """% pixeles con SCL en {4=veg, 5=suelo, 6=agua, 7=unclass} (no nubes/sombras)."""
    scl = tile[bands.index("SCL")]
    return float(np.isin(scl, [4, 5, 6, 7]).mean())


def generar_texto(clase: str, no2: float, so2: float, o3: float, ndvi: float) -> str:
    return {
        "contaminacion_alta_NO2": (
            f"Zona urbana con NO2 alto ({no2:.2e} mol/m2), trafico vehicular intenso."),
        "contaminacion_alta_SO2": (
            f"Pluma industrial con SO2 elevado ({so2:.2e} mol/m2), corredor Yumbo-Acopi."),
        "ozono_anomalo": (
            f"Anomalia de ozono ({o3:.2e} mol/m2), fotoquimica activa."),
        "vegetacion_densa": (
            f"Vegetacion densa, NDVI={ndvi:.2f}, cana de azucar o bosque."),
        "suelo_urbano": (
            f"Zona urbana construida, NDVI={ndvi:.2f}, alta densidad edificada."),
    }[clase]


# ---------------------------------------------------------------------------
# Reglas de clase


def cand_cumple(cand: TileCand, clase: str, perc: dict) -> bool:
    cont_ok = np.isfinite([cand.no2, cand.so2, cand.o3]).all()
    if clase == "contaminacion_alta_NO2":
        return cont_ok and cand.no2 > perc["NO2"]["p90"]
    if clase == "contaminacion_alta_SO2":
        return cont_ok and cand.so2 > perc["SO2"]["p90"]
    if clase == "ozono_anomalo":
        return (cont_ok and cand.o3 > 0 and
                (cand.o3 < perc["O3"]["p10"] or cand.o3 > perc["O3"]["p90"]))
    if clase == "vegetacion_densa":
        return np.isfinite(cand.ndvi) and cand.ndvi > 0.6
    if clase == "suelo_urbano":
        return (np.isfinite(cand.ndvi) and np.isfinite(cand.ndbi)
                and cand.ndvi < 0.2 and cand.ndbi > 0.0)
    return False


def evaluar_candidato(cand: TileCand, s2, no2, so2, o3,
                      bands: list[str]) -> np.ndarray | None:
    """Llena el candidato con tile + features + valores S5P. Devuelve tile o None."""
    tile = extraer_tile(s2, cand)
    if tile.shape != (N_BANDAS_S2, TILE_PX, TILE_PX):
        return None
    cand.scl_pct = scl_valido(tile, bands)
    if cand.scl_pct < SCL_THRESHOLD:
        return None
    cand.ndvi = calc_ndvi(tile, bands)
    cand.ndbi = calc_ndbi(tile, bands)
    t_no2 = alinear_t(cand.time_s2, no2, "no2")
    t_so2 = alinear_t(cand.time_s2, so2, "so2")
    t_o3  = alinear_t(cand.time_s2, o3,  "o3")
    cand.no2 = valor_s5p(no2, cand.lat, cand.lon,
                         "tropospheric_NO2_column_number_density", t_no2)
    cand.so2 = valor_s5p(so2, cand.lat, cand.lon,
                         "SO2_column_number_density", t_so2)
    cand.o3  = valor_s5p(o3,  cand.lat, cand.lon,
                         "O3_column_number_density", t_o3)
    return tile


# ---------------------------------------------------------------------------
# Pipeline target-driven


def proponer_un_candidato(s2, rng) -> TileCand:
    half = TILE_PX // 2
    t = int(rng.integers(0, s2.sizes["time"]))
    y = int(rng.integers(half, s2.sizes["y"] - half))
    x = int(rng.integers(half, s2.sizes["x"] - half))
    return TileCand(
        time_idx_s2=t, time_s2=str(s2["time"].values[t]),
        y_idx=y, x_idx=x,
        lat=float(s2["y"].values[y]),
        lon=float(s2["x"].values[x]),
    )


def run(n_tiles: int, dry_run: bool, max_intentos_factor: int = 80):
    rng = np.random.default_rng(SEED)
    t0 = time.time()

    s2  = abrir_panel("copernicus_s2_sr_harmonized")
    no2 = abrir_panel("copernicus_s5p_offl_l3_no2")
    so2 = abrir_panel("copernicus_s5p_offl_l3_so2")
    o3  = abrir_panel("copernicus_s5p_offl_l3_o3")
    log.info(f"Paneles abiertos en {time.time()-t0:.1f}s")
    log.info(f"  S2:  {dict(s2.sizes)}")
    log.info(f"  NO2: {dict(no2.sizes)} | SO2: {dict(so2.sizes)} | O3: {dict(o3.sizes)}")

    _ = times_parseados(no2, "no2")
    _ = times_parseados(so2, "so2")
    _ = times_parseados(o3,  "o3")

    dagma_df, est = cargar_dagma()
    log.info(f"DAGMA: {len(dagma_df):,} filas, {len(est)} estaciones")

    t0 = time.time()
    perc = calcular_percentiles_s5p(no2, so2, o3, n_sample=500, rng=rng)
    log.info(f"Percentiles ({time.time()-t0:.1f}s):")
    for g, p in perc.items():
        log.info(f"  {g}: p10={p['p10']:.3e} p50={p['p50']:.3e} "
                 f"p90={p['p90']:.3e} p99={p['p99']:.3e}  (n={p['n_validos']:,})")

    bands = s2["band"].values.tolist()
    obj_por_clase = max(1, n_tiles // len(CLASES))
    aceptados = {c: [] for c in CLASES}
    eval_stats = {"propuestos": 0, "rj_scl": 0, "rj_shape": 0, "evaluados_ok": 0}

    t0_total = time.time()
    for clase in CLASES:
        max_intentos = obj_por_clase * max_intentos_factor
        intentos = 0
        t0_clase = time.time()
        while len(aceptados[clase]) < obj_por_clase and intentos < max_intentos:
            cand = proponer_un_candidato(s2, rng)
            tile = evaluar_candidato(cand, s2, no2, so2, o3, bands)
            intentos += 1
            eval_stats["propuestos"] += 1
            if tile is None:
                if (not np.isfinite(cand.scl_pct)) or cand.scl_pct < SCL_THRESHOLD:
                    eval_stats["rj_scl"] += 1
                else:
                    eval_stats["rj_shape"] += 1
                continue
            eval_stats["evaluados_ok"] += 1
            if cand_cumple(cand, clase, perc):
                cand.clase = clase
                aceptados[clase].append((cand, tile))

            if intentos % 200 == 0:
                log.info(f"  [{clase}] intentos {intentos}/{max_intentos}, "
                         f"aceptados {len(aceptados[clase])}/{obj_por_clase}")

        log.info(f"  clase {clase}: {len(aceptados[clase])}/{obj_por_clase} "
                 f"en {time.time()-t0_clase:.1f}s ({intentos} intentos)")

    log.info(f"Total iteracion: {time.time()-t0_total:.1f}s")
    log.info(f"  propuestos:    {eval_stats['propuestos']}")
    log.info(f"  rechazados SCL:{eval_stats['rj_scl']}")
    log.info(f"  rechazados shp:{eval_stats['rj_shape']}")
    log.info(f"  evaluados OK:  {eval_stats['evaluados_ok']}")

    total_ok = 0
    for c, lst in aceptados.items():
        for cand, tile in lst:
            assert tile.shape == (N_BANDAS_S2, TILE_PX, TILE_PX)
            assert tile.dtype == np.float32
            total_ok += 1
    log.info(f"Validacion: {total_ok} tiles OK")

    if dry_run:
        log.info(">>> Modo dry-run: NO se guarda nada.")
        return aceptados, perc, eval_stats

    log.info("Armando tiles_train.npz y tiles_meta.parquet...")
    todos = [(c, cand, tile) for c, lst in aceptados.items() for cand, tile in lst]
    tiles_arr = np.stack([t for _, _, t in todos])
    meta = pd.DataFrame([{
        "clase": c, "time_s2": cand.time_s2,
        "lat": cand.lat, "lon": cand.lon,
        "ndvi": cand.ndvi, "ndbi": cand.ndbi, "scl_pct": cand.scl_pct,
        "no2": cand.no2, "so2": cand.so2, "o3": cand.o3,
        "texto": generar_texto(c, cand.no2, cand.so2, cand.o3, cand.ndvi),
    } for c, cand, _ in todos])

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUT_DIR / "tiles_train.npz",
                        data=tiles_arr, bands=np.array(bands))
    meta.to_parquet(OUT_DIR / "tiles_meta.parquet")
    log.info(f"Guardado: tiles_train.npz ({tiles_arr.nbytes/1024**2:.1f} MB) + "
             f"tiles_meta.parquet ({len(meta)} filas) en {OUT_DIR}")
    return aceptados, perc, eval_stats
