import os
import sys
import ee

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from config import PROJECT_ID, FUENTES, CALI  # type: ignore[reportMissingImports]
from logger import get_logger                  # type: ignore[reportMissingImports]

log = get_logger('ver_archivos_cali')
ee.Initialize(project=PROJECT_ID)

region = ee.Geometry.Rectangle(CALI)

for fuente in FUENTES:
    imagen = (ee.ImageCollection(fuente)
              .filterBounds(region)
              .filterDate('2021-04', '2026-04')
              .first()
              .clip(region))
    info = imagen.getInfo()

    resumen = {
        'fuente': fuente,
        'id': info.get('id'),
        'fecha': info['properties'].get('system:time_start'),
        'num_bandas': len(info['bands']),
        'recortado_a': CALI,
    }
    log.info(f"{resumen}")
