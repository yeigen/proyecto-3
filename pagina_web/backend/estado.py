"""Estado global del backend estático.

Carga en memoria los artefactos pre-computados de Sit 3 (grids, estaciones,
validación) al iniciar el servidor. No carga modelos de deep learning:
las predicciones ya están pre-computadas en la malla de inferencia
ConvLSTM + Kriging generada en notebooks/sit3/01-convlstm.ipynb.
"""

import json
import logging
from backend import config

logger = logging.getLogger(__name__)

datos = {}


def _cargar_json(ruta, default):
    if ruta.exists():
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    logger.warning(f"No encontrado: {ruta}")
    return default


def cargar_artefactos():
    datos["grids"] = _cargar_json(config.GRIDS_JSON, {})
    datos["estaciones"] = _cargar_json(config.ESTACIONES_JSON, [])
    datos["lisa"] = _cargar_json(config.LISA_JSON, {})
    datos["variogramas"] = _cargar_json(config.VARIOGRAMAS_JSON, {})
    datos["perfiles"] = _cargar_json(config.PERFILES_JSON, {})
    datos["loocv"] = _cargar_json(config.LOOCV_JSON, [])
    datos["kpis"] = _cargar_json(config.KPIS_JSON, [])
    logger.info(
        f"Artefactos Sit 3 cargados: {len(datos['grids'])} grids, "
        f"{len(datos['estaciones'])} estaciones, {len(datos['kpis'])} KPIs"
    )
    return datos
