import time
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.config import BBOX, CLASE_DESCRIPCION
from backend.data.loader import buscar_tile_cercano, preprocesar_tile
from backend.modelo.clip_sae import generar_embedding
from backend.estado import modelo_global, DISPOSITIVO

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/predict", tags=["prediccion"])


class PredictRequest(BaseModel):
    lat: float = Field(..., ge=BBOX[1], le=BBOX[3],
                       description="Latitud del punto en Cali",
                       examples=[3.45, 3.52, 3.31])
    lon: float = Field(..., ge=BBOX[0], le=BBOX[2],
                       description="Longitud del punto en Cali",
                       examples=[-76.53, -76.49, -76.56])
    contaminante: str = Field(default="NO2", pattern="^(NO2|SO2|O3)$",
                              description="Contaminante (solo referencia, aun no afecta la prediccion)",
                              examples=["NO2", "SO2", "O3"])
    horizonte: str = Field(default="T+1", pattern="^(T\\+1|T\\+3|T\\+7)$",
                           description="Horizonte temporal (solo referencia, aun no afecta la prediccion)",
                           examples=["T+1", "T+3", "T+7"])


@router.post("")
async def predecir_punto(req: PredictRequest):
    if "visual" not in modelo_global:
        raise HTTPException(503, "Modelo no cargado")

    t0 = time.perf_counter()
    visual = modelo_global["visual"]
    fusion = modelo_global["fusion"]
    band_mean = modelo_global["band_mean"]
    band_std = modelo_global["band_std"]

    try:
        tile, meta, idx = buscar_tile_cercano(req.lat, req.lon)
        tile_tensor = preprocesar_tile(tile, band_mean, band_std)
        emb = generar_embedding(visual, fusion, tile_tensor, DISPOSITIVO)
    except Exception as e:
        logger.error(f"Error en predicción: {e}")
        raise HTTPException(500, f"Error generando embedding: {e}")

    latencia_ms = round((time.perf_counter() - t0) * 1000)

    return {
        "lat": req.lat,
        "lon": req.lon,
        "contaminante": req.contaminante,
        "horizonte": req.horizonte,
        "tile_id": int(idx),
        "tile_lat": round(float(meta["lat"]), 4),
        "tile_lon": round(float(meta["lon"]), 4),
        "clase": str(meta["clase"]),
        "clase_descripcion": CLASE_DESCRIPCION.get(str(meta["clase"]), ""),
        "ndvi": round(float(meta.get("ndvi", 0) or 0), 4),
        "embedding_dim": 512,
        "embedding_sample": [round(float(v), 4) for v in emb[0].tolist()[:8]],
        "latencia_ms": latencia_ms,
    }


@router.post("/grid")
async def predecir_grilla():
    raise HTTPException(
        status_code=501,
        detail="Grid de predicciones no disponible. Pendiente de ConvLSTM + Kriging.",
    )
