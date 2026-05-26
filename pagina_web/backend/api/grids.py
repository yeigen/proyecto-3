"""Endpoint de overlays de mapas (PNG georreferenciados para Leaflet ImageOverlay)."""

import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.config import OVERLAYS_DIR, GASES_CON_MAPA
from backend.estado import datos

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/grids", tags=["grids"])


def _norm_horizonte(h):
    h = h.strip().replace(" ", "+")
    if not h.startswith("T"):
        h = "T" + h
    if "+" not in h:
        h = "T+" + h[1:]
    return h


# La ruta /bounds/... se define ANTES de /{contaminante}/... para evitar colisión
@router.get("/bounds/{contaminante}/{horizonte}")
async def bounds_overlay(contaminante: str, horizonte: str):
    """Devuelve bounds [lat_min, lon_min, lat_max, lon_max] para posicionar el overlay."""
    grids = datos.get("grids", {})
    key = f"{contaminante}_{_norm_horizonte(horizonte)}"
    if key not in grids:
        raise HTTPException(404, f"Mapa no disponible para {key}")
    g = grids[key]
    return {"bounds": g["bounds"], "vmin": g["vmin"], "vmax": g["vmax"]}


@router.get("/{contaminante}/{horizonte}/{capa}")
async def servir_overlay(contaminante: str, horizonte: str, capa: str):
    """Sirve el PNG del overlay. capa = 'pred' (predicción) o 'sigma' (incertidumbre)."""
    if contaminante not in GASES_CON_MAPA:
        raise HTTPException(422, f"{contaminante} sin overlay. Disponibles: {GASES_CON_MAPA}")
    if capa not in ("pred", "sigma"):
        raise HTTPException(422, "capa debe ser 'pred' o 'sigma'")
    h = _norm_horizonte(horizonte).replace("+", "")  # T+1 -> T1 (nombre de archivo)
    archivo = OVERLAYS_DIR / f"{contaminante}_{h}_{capa}.png"
    if not archivo.exists():
        raise HTTPException(404, f"Overlay no encontrado: {archivo.name}")
    return FileResponse(archivo, media_type="image/png")
