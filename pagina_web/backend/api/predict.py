"""Endpoints de predicción servidos desde la malla pre-computada de Sit 3.

El pipeline ConvLSTM + ST-Kriging se ejecuta offline (notebooks/sit3/01-convlstm.ipynb)
y genera una malla de inferencia de ~1296 celdas por (gas, horizonte). Estos
endpoints sirven esa malla: /predict devuelve el punto más cercano, /predict/grid
devuelve toda la grilla. Latencia <100ms (muy bajo el umbral PDF de 8s).
"""

import time
import math
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.config import BBOX, CONTAMINANTES, HORIZONTES, GASES_CON_MAPA
from backend.estado import datos

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/predict", tags=["prediccion"])


class PredictRequest(BaseModel):
    lat: float = Field(..., ge=BBOX[1], le=BBOX[3], examples=[3.45, 3.52, 3.31])
    lon: float = Field(..., ge=BBOX[0], le=BBOX[2], examples=[-76.53, -76.49, -76.56])
    contaminante: str = Field(default="SO2", pattern="^(NO2|SO2|O3)$", examples=["SO2", "O3"])
    horizonte: str = Field(default="T+1", pattern="^(T\\+1|T\\+3|T\\+7)$", examples=["T+1", "T+3", "T+7"])


def _norm_horizonte(h):
    # El '+' en URLs se decodifica como espacio; normalizar a 'T+N'
    h = h.strip().replace(" ", "+")
    if not h.startswith("T"):
        h = "T" + h
    if "+" not in h:  # 'T1' -> 'T+1'
        h = "T+" + h[1:]
    return h


def _grid_key(contaminante, horizonte):
    # grids_prediccion.json usa claves tipo "SO2_T+1"
    return f"{contaminante}_{_norm_horizonte(horizonte)}"


@router.post("")
async def predecir_punto(req: PredictRequest):
    t0 = time.perf_counter()

    if req.contaminante == "NO2":
        raise HTTPException(
            422,
            "NO2 no tiene mapa de Kriging: solo 2 estaciones DAGMA lo miden "
            "(Universidad del Valle, Yumbo), insuficiente para variograma (n>=3). "
            "Disponible: SO2, O3.",
        )

    grids = datos.get("grids", {})
    key = _grid_key(req.contaminante, req.horizonte)
    if key not in grids:
        raise HTTPException(404, f"Mapa no disponible para {key}. Disponibles: {list(grids.keys())}")

    celdas = grids[key]["celdas"]
    # Vecino más cercano (distancia euclidiana en grados)
    mejor = min(celdas, key=lambda c: (c["lat"] - req.lat) ** 2 + (c["lon"] - req.lon) ** 2)
    dist_km = math.sqrt((mejor["lat"] - req.lat) ** 2 + (mejor["lon"] - req.lon) ** 2) * 111

    latencia_ms = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "lat": req.lat,
        "lon": req.lon,
        "contaminante": req.contaminante,
        "horizonte": req.horizonte,
        "valor": mejor["valor"],
        "varianza": mejor["varianza"],
        "sigma": round(math.sqrt(max(mejor["varianza"], 0)), 3),
        "celda_lat": mejor["lat"],
        "celda_lon": mejor["lon"],
        "dist_celda_km": round(dist_km, 3),
        "unidad": "ug/m3",
        "latencia_ms": latencia_ms,
    }


@router.post("/grid")
@router.get("/grid")
async def predecir_grilla(contaminante: str = "SO2", horizonte: str = "T+1"):
    if contaminante not in GASES_CON_MAPA:
        raise HTTPException(422, f"{contaminante} sin mapa. Disponibles: {GASES_CON_MAPA}")
    grids = datos.get("grids", {})
    key = _grid_key(contaminante, horizonte)
    if key not in grids:
        raise HTTPException(404, f"Mapa no disponible para {key}")
    g = grids[key]
    homogeneo = abs(g["vmax"] - g["vmin"]) < 1e-3
    return {
        "contaminante": contaminante,
        "horizonte": horizonte,
        "celdas": g["celdas"],
        "bounds": g["bounds"],
        "vmin": g["vmin"],
        "vmax": g["vmax"],
        "n_celdas": g["n_celdas"],
        "homogeneo": homogeneo,
        "nota": (
            f"Superficie homogénea ({g['vmin']} ug/m3): variograma de residuos nugget puro, "
            "el modelo capturó toda la estructura espacial."
        ) if homogeneo else None,
    }
