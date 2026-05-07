import os
import sys
import math
import ee

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from config import PROJECT_ID, FUENTES, CALI  # type: ignore[reportMissingImports]
from logger import get_logger                  # type: ignore[reportMissingImports]

log = get_logger('explorar_metadata_cali')
ee.Initialize(project=PROJECT_ID)

region = ee.Geometry.Rectangle(CALI)

BYTES_DTYPE = {
    'int8': 1, 'uint8': 1,
    'int16': 2, 'uint16': 2,
    'int32': 4, 'uint32': 4, 'float': 4, 'float32': 4,
    'int64': 8, 'uint64': 8, 'double': 8, 'float64': 8,
}

xmin, ymin, xmax, ymax = CALI
lat_media = (ymin + ymax) / 2
ancho_m = (xmax - xmin) * 111_320 * math.cos(math.radians(lat_media))
alto_m = (ymax - ymin) * 110_540

log.info(f"BBox Cali: ~{ancho_m/1000:.1f} km x {alto_m/1000:.1f} km")

for fuente in FUENTES:
    primera = (ee.ImageCollection(fuente)
               .filterBounds(region)
               .filterDate('2021-04', '2026-04')
               .first())
    info = primera.getInfo()
    bandas = info.get('bands', [])
    nombres = [b['id'] for b in bandas]
    dtypes = [b.get('data_type', {}).get('precision', '?') for b in bandas]

    escala_m = primera.select(0).projection().nominalScale().getInfo()
    ancho_px = math.ceil(ancho_m / escala_m)
    alto_px = math.ceil(alto_m / escala_m)
    bytes_px = sum(
        BYTES_DTYPE.get(b.get('data_type', {}).get('precision', ''), 4)
        for b in bandas
    )
    peso_estimado = ancho_px * alto_px * bytes_px

    log.info(f"FUENTE: {fuente}")
    log.info(f"  Recortado a Cali bbox: {CALI}")
    log.info(f"  Resolucion nativa:      {escala_m:.2f} m/px")
    log.info(f"  Dimensiones recorte:    {ancho_px} x {alto_px} px ({ancho_px*alto_px:,} px)")
    log.info(f"  Bandas ({len(nombres)}): {nombres}")
    log.info(f"  Dtypes:                 {dtypes}")
    log.info(f"  Peso por imagen (raw):  {peso_estimado:,} bytes ({peso_estimado/1024:.2f} KB)")
