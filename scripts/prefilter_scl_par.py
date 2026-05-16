"""
Pre-filtrado SCL paralelo usando ThreadPoolExecutor (no fork, sin problemas gRPC).
"""

from __future__ import annotations
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import gcsfs
import numpy as np
import pandas as pd
import xarray as xr

BUCKET = "fuentes-proyecto-3"
ZARR_PATH = f"{BUCKET}/copernicus_s2_sr_harmonized/panel.zarr"
OUT_CSV = Path("scl_por_escena.csv")
N_WORKERS = 16
SCL_VALIDAS = [4, 5, 6, 7]


def main():
    fs = gcsfs.GCSFileSystem(token="google_default")
    s2 = xr.open_zarr(fs.get_mapper(ZARR_PATH), consolidated=True)
    n_t = s2.sizes["time"]
    scl = s2["data"].sel(band="SCL")
    times_vals = s2["time"].values
    print(f"Procesando {n_t} escenas con {N_WORKERS} threads...", flush=True)

    def worker(t_idx: int):
        arr = scl.isel(time=t_idx).values
        finite = np.isfinite(arr)
        if not finite.any():
            return t_idx, str(times_vals[t_idx]), np.nan
        validos = np.isin(arr, SCL_VALIDAS) & finite
        return t_idx, str(times_vals[t_idx]), float(validos.sum() / finite.sum())

    t0 = time.time()
    results = []
    with ThreadPoolExecutor(max_workers=N_WORKERS) as ex:
        futures = {ex.submit(worker, t): t for t in range(n_t)}
        done = 0
        for fut in as_completed(futures):
            try:
                t_idx, time_s2, pct = fut.result()
                results.append((t_idx, time_s2, pct))
            except Exception as e:
                t = futures[fut]
                print(f"  ERROR t={t}: {e}", flush=True)
                results.append((t, "", np.nan))
            done += 1
            if done % 50 == 0 or done == n_t:
                elapsed = time.time() - t0
                rate = done / elapsed
                eta = (n_t - done) / rate / 60 if rate > 0 else 0
                print(f"  {done}/{n_t} ({rate:.1f} esc/s, ETA {eta:.1f} min)", flush=True)

    elapsed = time.time() - t0
    print(f"\nCompletado en {elapsed/60:.1f} min ({n_t/elapsed:.1f} esc/s)", flush=True)

    df = pd.DataFrame(results, columns=["time_idx", "time_s2", "scl_pct"])
    df = df.sort_values("time_idx").reset_index(drop=True)
    df.to_csv(OUT_CSV, index=False)

    pcts = df["scl_pct"].values
    valid_pcts = pcts[np.isfinite(pcts)]
    print(f"\nStats ({len(valid_pcts)}/{n_t} escenas con dato valido):", flush=True)
    print(f"  pct medio: {np.mean(valid_pcts):.3f}", flush=True)
    print(f"  > 0.3: {(pcts > 0.3).sum()} escenas", flush=True)
    print(f"  > 0.5: {(pcts > 0.5).sum()} escenas", flush=True)
    print(f"  > 0.7: {(pcts > 0.7).sum()} escenas", flush=True)
    print(f"\nGuardado en {OUT_CSV.resolve()}", flush=True)


if __name__ == "__main__":
    main()
