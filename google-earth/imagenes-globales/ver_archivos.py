import os
import sys
import ee

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from config import PROJECT_ID, FUENTES  # type: ignore[reportMissingImports]
from logger import get_logger            # type: ignore[reportMissingImports]

log = get_logger('ver_archivos')
ee.Initialize(project=PROJECT_ID)

for fuentes in FUENTES:
    imagen = ee.ImageCollection(fuentes).filterDate('2021-04', '2026-04').first()
    info = imagen.getInfo()

    resumen = {
        'fuente': fuentes,
        'id': info['id'],
        'fecha': info['properties']['system:time_start'],
        'num_bandas': len(info['bands']),
    }
    log.info(f"{resumen}")
