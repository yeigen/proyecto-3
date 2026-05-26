import logging
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/validate", tags=["validacion"])


@router.get("")
async def validar_loo():
    raise HTTPException(
        status_code=501,
        detail=(
            "Validaci\u00f3n LOO-CV no disponible. "
            "Depende de /api/predict para generar predicciones. "
            "El c\u00f3digo de Kriging y c\u00e1lculo de RMSE/MAE/R\u00b2 est\u00e1 listo en "
            "backend/modelo/kriging.py y requiere datos del pipeline completo."
        ),
    )
