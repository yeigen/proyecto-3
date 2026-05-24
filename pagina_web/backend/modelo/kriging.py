import numpy as np
from pykrige.ok3d import OrdinaryKriging3D
from libpysal import weights
from esda import Moran, Moran_Local


def st_kriging(
    lats: np.ndarray,
    lons: np.ndarray,
    times: np.ndarray,
    values: np.ndarray,
    q_lats: np.ndarray,
    q_lons: np.ndarray,
    q_t: np.ndarray | float,
    variogram: str = "exponential",
) -> tuple[np.ndarray, np.ndarray]:
    lat_mean, lat_std = lats.mean(), lats.std()
    lon_mean, lon_std = lons.mean(), lons.std()
    t_mean, t_std = times.mean(), times.std() + 1e-8

    lat_n = (lats - lat_mean) / lat_std
    lon_n = (lons - lon_mean) / lon_std
    t_n = (times - t_mean) / t_std

    if np.isscalar(q_t):
        q_t_n = (q_t - t_mean) / t_std
    else:
        q_t_n = (q_t - t_mean) / t_std

    ok = OrdinaryKriging3D(
        lat_n, lon_n, t_n, values,
        variogram_model=variogram,
        verbose=False,
    )

    z, var = ok.execute(
        "points",
        (q_lats - lat_mean) / lat_std,
        (q_lons - lon_mean) / lon_std,
        q_t_n,
    )
    return z, var


def moran_global(predicciones: np.ndarray, lats: np.ndarray, lons: np.ndarray) -> dict:
    w = weights.distance.DistanceBand(
        np.column_stack([lons, lats]), threshold=0.02, binary=True
    )
    w.transform = "r"
    mi = Moran(predicciones.flatten(), w)
    return {
        "I": round(float(mi.I), 4),
        "p_value": round(float(mi.p_sim), 4),
        "significativo": bool(mi.p_sim < 0.05),
    }


def moran_lisa(predicciones: np.ndarray, lats: np.ndarray, lons: np.ndarray) -> dict:
    w = weights.distance.DistanceBand(
        np.column_stack([lons, lats]), threshold=0.02, binary=True
    )
    w.transform = "r"
    lisa = Moran_Local(predicciones.flatten(), w)
    clusters = []
    for i in range(len(lisa.q)):
        clusters.append({
            "quadrant": int(lisa.q[i]),
            "p_value": round(float(lisa.p_sim[i]), 4),
            "significativo": bool(lisa.p_sim[i] < 0.05),
        })
    return {"clusters": clusters}
