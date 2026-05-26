import logging
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/grids", tags=["grids"])


@router.get("/{contaminante}/{horizonte}")
async def servir_geotiff(contaminante: str, horizonte: str):
    raise HTTPException(
        status_code=501,
        detail=(
            "GeoTIFF no disponible. "
            "Requiere ejecutar /api/predict/grid primero para generar los rasters. "
            "El c\u00f3digo de generaci\u00f3n con rasterio est\u00e1 listo en backend/api/grids.py."
        ),
    )
