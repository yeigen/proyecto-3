"""
Pre-filtrado de escenas Sentinel-2 por nubosidad. Para correr EN EL DROPLET
con acceso a GCS (proyecto charming-mile-436804-q2).

Lee la banda SCL del panel S2 en gs://fuentes-proyecto-3 y calcula la
fraccion de pixeles validos (SCL in {4,5,6,7}) por escena. Guarda CSV con
2 columnas: time_idx, scl_pct.

Tiempo esperado: 10-15 min sobre 1,552 escenas leyendo desde GCS us-central1.

Uso:
    ssh root@192.241.132.222
    cd /root/proyecto-3
    .venv/bin/python scripts/prefilter_scl.py
    # genera /root/proyecto-3/scl_por_escena.csv

Despues:
    # Subir a Kaggle Dataset (vez de subir todo el dataset, solo el csv)
    kaggle datasets metadata juanjoseorozcolopez/geovision-fuentes -p /tmp/
    cp scl_por_escena.csv /tmp/
    kaggle datasets version -p /tmp -m "add scl_por_escena.csv (pre-filter S2)"
"""

from __future__ import annotations

import time
from pathlib import Path

import gcsfs
import numpy as np
import pandas as pd
import xarray as xr
from tqdm import tqdm


BUCKET = "fuentes-proyecto-3"
ZARR_PATH = f"{BUCKET}/copernicus_s2_sr_harmonized/panel.zarr"
OUT_CSV = Path("scl_por_escena.csv")

# Categorias SCL validas (no nube/no sombra)
SCL_VALIDAS = [4, 5, 6, 7]


def main():
    print(f"Abriendo Zarr en gs://{ZARR_PATH}...")
    fs = gcsfs.GCSFileSystem()
    s2 = xr.open_zarr(fs.get_mapper(ZARR_PATH), consolidated=True)
    print(f"  shape: {dict(s2.sizes)}")

    n_t = s2.sizes["time"]
    scl = s2["data"].sel(band="SCL")  # (1552, 3897, 3897)

    # Procesar timestep por timestep
    # Cada timestep son ~60 MB (3897x3897 float32). En memoria cabe.
    pcts = np.zeros(n_t, dtype="float32")
    t0 = time.time()
    for i in tqdm(range(n_t), desc="Calculando SCL pct"):
        arr = scl.isel(time=i).values  # baja 1 timestep entero (~4 chunks Zarr)
        # SCL pct = fraccion de pixeles validos sobre los no-NaN
        finite = np.isfinite(arr)
        if not finite.any():
            pcts[i] = np.nan
            continue
        validos = np.isin(arr, SCL_VALIDAS) & finite
        pcts[i] = validos.sum() / finite.sum()

    elapsed = time.time() - t0
    print(f"\nCompletado en {elapsed/60:.1f} min")

    # Stats
    print(f"  SCL pct medio: {np.nanmean(pcts):.3f}")
    print(f"  SCL pct > 0.5: {(pcts > 0.5).sum()} escenas")
    print(f"  SCL pct > 0.7: {(pcts > 0.7).sum()} escenas")
    print(f"  SCL pct > 0.3: {(pcts > 0.3).sum()} escenas")

    # Guardar
    df = pd.DataFrame({
        "time_idx": np.arange(n_t),
        "time_s2": [str(t) for t in s2["time"].values],
        "scl_pct": pcts,
    })
    df.to_csv(OUT_CSV, index=False)
    print(f"\nGuardado en {OUT_CSV.resolve()} ({OUT_CSV.stat().st_size/1024:.1f} KB)")


if __name__ == "__main__":
    main()
