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
