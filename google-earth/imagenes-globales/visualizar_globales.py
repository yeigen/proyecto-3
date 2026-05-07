import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

import ee
from config import PROJECT_ID, FUENTES, BANDAS_UTILES  # type: ignore[reportMissingImports]
from logger import get_logger                          # type: ignore[reportMissingImports]

log = get_logger('visualizar_globales')
ee.Initialize(project=PROJECT_ID)

OUT = os.path.join(HERE, 'imagenes-reales')
os.makedirs(OUT, exist_ok=True)

# Una imagen representativa por fuente, sin recorte a Cali (vista global)
VIZ = {
    'COPERNICUS/S5P/OFFL/L3_NO2': {
        'bands': ['tropospheric_NO2_column_number_density'],
        'min': 0, 'max': 0.0002,
        'palette': ['black', 'blue', 'purple', 'cyan', 'green', 'yellow', 'red'],
    },
    'COPERNICUS/S5P/OFFL/L3_SO2': {
        'bands': ['SO2_column_number_density'],
        'min': 0, 'max': 0.0005,
        'palette': ['black', 'blue', 'purple', 'cyan', 'green', 'yellow', 'red'],
    },
    'COPERNICUS/S5P/OFFL/L3_O3': {
        'bands': ['O3_column_number_density'],
        'min': 0.12, 'max': 0.15,
        'palette': ['blue', 'cyan', 'green', 'yellow', 'red'],
    },
    'COPERNICUS/S2_SR_HARMONIZED': {
        'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 0.3,
    },
    'ECMWF/ERA5/HOURLY': {
        'bands': ['temperature_2m'], 'min': 250, 'max': 320,
        'palette': ['blue', 'cyan', 'green', 'yellow', 'red'],
    },
    'MODIS/061/MCD19A2_GRANULES': {
        'bands': ['Optical_Depth_047'], 'min': 0, 'max': 500,
        'palette': ['black', 'blue', 'purple', 'cyan', 'green', 'yellow', 'red'],
    },
}

for fuente_id in FUENTES:
    nombre = fuente_id.split('/')[-1].lower()
    log.info(f"Procesando: {fuente_id}")
    try:
        col = ee.ImageCollection(fuente_id).filterDate('2024-01-01', '2024-06-01')

        if fuente_id.startswith('COPERNICUS/S5P'):
            imagen = col.mean()
        elif fuente_id == 'COPERNICUS/S2_SR_HARMONIZED':
            # S2 tileado. 1 mes + median sobre Colombia.
            s2_col = (ee.ImageCollection(fuente_id)
                      .filterDate('2024-01-01', '2024-01-31')
                      .filterBounds(ee.Geometry.Rectangle([-79, -4, -67, 12])))
            imagen = s2_col.median().divide(10000)
        elif fuente_id == 'MODIS/061/MCD19A2_GRANULES':
            # MODIS granulado. 1 mes + median Sudamerica.
            m_col = (ee.ImageCollection(fuente_id)
                     .filterDate('2024-01-01', '2024-01-31')
                     .filterBounds(ee.Geometry.Rectangle([-85, -60, -30, 15])))
            imagen = m_col.median()
        else:
            imagen = col.first()

        viz = VIZ[fuente_id]
        imagen = imagen.select(viz['bands']).unmask(viz.get('min', 0))

        thumb = {**viz, 'dimensions': 512, 'format': 'png'}
        filename = os.path.join(OUT, f'{nombre}.png')
        urllib.request.urlretrieve(imagen.getThumbURL(thumb), filename)
        log.info(f"  ✓ {nombre}.png")

    except Exception as exc:
        log.warning(f"  ✗ {fuente_id}: {exc}")

log.info(f"Directorio: {OUT}")
