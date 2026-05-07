import os
import sys
import ee

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from config import PROJECT_ID, FUENTES  # type: ignore[reportMissingImports]
from logger import get_logger            # type: ignore[reportMissingImports]

log = get_logger('explorar_metadata')
ee.Initialize(project=PROJECT_ID)

for fuentes in FUENTES:
    imagen = ee.ImageCollection(fuentes).filterDate('2021-04', '2026-04').first().getInfo()
    bandas = imagen.get('bands', [])
    dimensiones = bandas[0].get('dimensions', 'No disponible')

    crs_transform = bandas[0].get('crs_transform', [])
    if len(crs_transform) >= 5:
        res_x = abs(crs_transform[0])
        res_y = abs(crs_transform[4])
        resolucion = f"{res_x} x {res_y} metros/pixel"
    else:
        resolucion = 'No disponible'

    nombres_bandas = [b['id'] for b in bandas]
    props = imagen.get('properties', {})
    peso_bytes = props.get('system:asset_size')
    peso_mb = peso_bytes / (1024 * 1024)
    peso_gb = peso_bytes / (1024 * 1024 * 1024)
    peso_str = f"{peso_bytes} bytes ({peso_mb:.2f} MB / {peso_gb:.2f} GB)"

    log.info(f"FUENTE: {fuentes}")
    log.info(f"Tamaño de imagen (pixeles):    {dimensiones}")
    log.info(f"Resolucion:                    {resolucion}")
    log.info(f"Peso total estimado:           {peso_str}")
    log.info(f"Nombres de todas las bandas:   {nombres_bandas}")
