"""Tiles CLIP del dataset rescate-1500: GeoJSON y resumen por clase."""

import functools
import pandas as pd
from backend import config


@functools.lru_cache(maxsize=1)
def _tiles():
    return pd.read_parquet(config.TILES_META)


def tiles_clip_geojson(limite=1500):
    df = _tiles().head(limite)
    features = []
    for _, r in df.iterrows():
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [float(r.lon), float(r.lat)]},
            "properties": {
                "clase": str(r.clase),
                "ndvi": round(float(r.get("ndvi", 0) or 0), 4),
                "ndbi": round(float(r.get("ndbi", 0) or 0), 4),
                "color": config.CLASE_COLOR_MAPA.get(str(r.clase), "#888888"),
            },
        })
    return {"type": "FeatureCollection", "features": features}


def resumen_clases():
    df = _tiles()
    return {str(k): int(v) for k, v in df.clase.value_counts().items()}


_ETIQUETAS = {
    "vegetacion_densa": "Vegetación densa",
    "suelo_urbano": "Suelo urbano",
    "contaminacion_alta_NO2": "Contaminación NO2 (tráfico)",
    "contaminacion_alta_SO2": "Contaminación SO2 (industria)",
    "ozono_anomalo": "Ozono anómalo",
}


def cobertura_en_punto(lat: float, lon: float, radio_km: float = 0.7, min_tiles: int = 3):
    """Qué tipo de zona/cobertura ve el modelo cerca de (lat, lon).

    Reusa los tiles CLIP (clase + NDVI/NDBI). Toma los tiles dentro del radio;
    si hay menos de `min_tiles`, cae a los k vecinos más cercanos.
    """
    df = _tiles()
    dgrados = radio_km / 111.0
    sub = df[df.lat.between(lat - dgrados, lat + dgrados) & df.lon.between(lon - dgrados, lon + dgrados)]
    if len(sub) < min_tiles:
        d2 = (df.lat - lat) ** 2 + (df.lon - lon) ** 2
        sub = df.loc[d2.nsmallest(min_tiles).index]

    conteos = {str(k): int(v) for k, v in sub.clase.value_counts().items()}
    if not conteos:
        return {"lat": lat, "lon": lon, "radio_km": radio_km, "n_tiles": 0,
                "clase_dominante": None, "etiqueta": "Sin datos", "descripcion": "",
                "ndvi": None, "ndbi": None, "clases": {}}

    dominante = max(conteos, key=conteos.get)
    ndvi = sub["ndvi"].mean() if "ndvi" in sub else None
    ndbi = sub["ndbi"].mean() if "ndbi" in sub else None
    return {
        "lat": lat, "lon": lon, "radio_km": radio_km, "n_tiles": int(len(sub)),
        "clase_dominante": dominante,
        "etiqueta": _ETIQUETAS.get(dominante, dominante),
        "descripcion": config.CLASE_DESCRIPCION.get(dominante, ""),
        "ndvi": round(float(ndvi), 3) if ndvi is not None and pd.notna(ndvi) else None,
        "ndbi": round(float(ndbi), 3) if ndbi is not None and pd.notna(ndbi) else None,
        "clases": conteos,
    }
