"""Endpoint de validación: LOO-CV, KPIs, LISA, variogramas, perfiles tipológicos."""

import logging
from fastapi import APIRouter
from backend.estado import datos

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/validate", tags=["validacion"])


@router.get("")
async def validar_loo():
    """Tabla LOO-CV por gas × horizonte + KPIs Sit 3."""
    return {
        "loocv": datos.get("loocv", []),
        "kpis": datos.get("kpis", []),
    }


@router.get("/lisa")
async def get_lisa():
    """Clusters LISA (HH/LL/HL/LH) por contaminante."""
    return datos.get("lisa", {})


@router.get("/variogramas")
async def get_variogramas():
    """Parámetros del variograma (nugget/sill/range) por contaminante."""
    return datos.get("variogramas", {})


@router.get("/perfiles")
async def get_perfiles():
    """Perfiles tipológicos K-Means de zonas crónicas."""
    return datos.get("perfiles", {})
