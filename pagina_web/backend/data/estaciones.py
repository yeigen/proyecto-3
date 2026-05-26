"""Datos de estaciones DAGMA: GeoJSON, promedios y cobertura temporal.

Lee del DAGMA limpio (df_dagma_unificado_coordenadas_limpias.parquet) con
coordenadas corregidas y 9 estaciones reales.
"""

import functools
import pandas as pd
from backend import config


@functools.lru_cache(maxsize=1)
def _dagma():
    df = pd.read_parquet(config.RUTA_DAGMA)
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["gas"] = df["tipo_gas"].str.upper()
    return df


@functools.lru_cache(maxsize=1)
def _estaciones_meta():
    return pd.read_csv(config.RUTA_ESTACIONES)


def estaciones_geojson():
    est = _estaciones_meta()
    dagma = _dagma()
    features = []
    for _, r in est.iterrows():
        gases = sorted(dagma[dagma.nombre_est == r.nombre_est].gas.unique().tolist())
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [float(r.longitud), float(r.latitud)]},
            "properties": {
                "id": str(r.nombre_est).replace(" ", "_"),
                "nombre": r.nombre_est,
                "altitud": float(r.get("altitud", 0) or 0),
                "contaminantes": gases,
            },
        })
    return {"type": "FeatureCollection", "features": features}


def promedios_contaminantes():
    dagma = _dagma()
    out = {}
    for est, sub in dagma.groupby("nombre_est"):
        prom = {}
        for gas in ["NO2", "SO2", "O3"]:
            vals = sub[sub.gas == gas].concentracion.dropna()
            if len(vals):
                prom[gas] = round(float(vals.mean()), 2)
        out[str(est).replace(" ", "_")] = prom
    return out


def coverage_por_anio():
    dagma = _dagma()
    conteo = dagma.groupby(dagma.fecha.dt.year).size()
    return {str(int(a)): int(n) for a, n in conteo.items()}
