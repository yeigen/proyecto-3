import os
import sys
import time
import math
import ee
from tqdm import tqdm

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from config import PROJECT_ID, FUENTES, CALI, ESCALA_OVERRIDE  # type: ignore[reportMissingImports]
from logger import get_logger                  # type: ignore[reportMissingImports]

log = get_logger('calcular_peso_cali')
ee.Initialize(project=PROJECT_ID)

ANIO_INICIO = 2021
ANIO_FIN = 2026
region = ee.Geometry.Rectangle(CALI)

BYTES_DTYPE = {
    'int8': 1, 'uint8': 1,
    'int16': 2, 'uint16': 2,
    'int32': 4, 'uint32': 4, 'float': 4, 'float32': 4,
    'int64': 8, 'uint64': 8, 'double': 8, 'float64': 8,
}

# bbox de Cali en metros (aprox lat-dependiente)
xmin, ymin, xmax, ymax = CALI
lat_media = (ymin + ymax) / 2
ancho_m = (xmax - xmin) * 111_320 * math.cos(math.radians(lat_media))
alto_m = (ymax - ymin) * 110_540
log.info(f"BBox Cali: ~{ancho_m/1000:.1f} km x {alto_m/1000:.1f} km")


def info_fuente(fuente):
    """Devuelve (escala_m, bytes_por_pixel_total, n_bandas, escala_nativa)."""
    primera = (ee.ImageCollection(fuente)
               .filterBounds(region)
               .filterDate(f'{ANIO_INICIO}-01-01', f'{ANIO_FIN}-01-01')
               .first())
    info = primera.getInfo()
    bandas = info.get('bands', [])
    escala_nativa = primera.select(0).projection().nominalScale().getInfo()
    escala_m = ESCALA_OVERRIDE.get(fuente, escala_nativa)
    bytes_px = sum(
        BYTES_DTYPE.get(b.get('data_type', {}).get('precision', ''), 4)
        for b in bandas
    )
    return escala_m, bytes_px, len(bandas), escala_nativa


def pixeles_recorte(escala_m):
    return math.ceil(ancho_m / escala_m) * math.ceil(alto_m / escala_m)


chunks = []
for anio in range(ANIO_INICIO, ANIO_FIN):
    for mes in range(1, 13):
        ini = f"{anio}-{mes:02d}-01"
        fin = f"{anio+1}-01-01" if mes == 12 else f"{anio}-{mes+1:02d}-01"
        chunks.append((ini, fin))

resumen = []
total_bytes = 0

log.info(f"Estimando peso REAL recortado a Cali ({len(FUENTES)} fuentes x {len(chunks)} meses)")

for fuente in FUENTES:
    log.info(f">>> {fuente}")
    t0 = time.time()
    try:
        escala_m, bytes_px, n_bandas, escala_nativa = info_fuente(fuente)
    except Exception as e:
        log.warning(f"  No se pudo obtener info: {e}")
        continue

    pixeles = pixeles_recorte(escala_m)
    peso_img = pixeles * bytes_px
    nota = f"{escala_m:.2f} m/px"
    if fuente in ESCALA_OVERRIDE:
        nota += f" (override; nominalScale={escala_nativa:.2f})"
    log.info(f"  Resolucion: {nota} | bandas: {n_bandas} "
             f"| pixeles bbox: {pixeles:,} | bytes/px: {bytes_px} "
             f"| peso/imagen: {peso_img/1024:.2f} KB")

    n_total = 0
    barra = tqdm(chunks, desc='  meses', unit='mes')
    for ini, fin in barra:
        col = (ee.ImageCollection(fuente)
               .filterBounds(region)
               .filterDate(ini, fin))
        n = col.size().getInfo() or 0
        n_total += n
        barra.set_postfix({'imgs': n_total})

    peso_total = n_total * peso_img
    dt = time.time() - t0
    total_bytes += peso_total
    resumen.append({
        'fuente': fuente,
        'escala': escala_m,
        'pixeles': pixeles,
        'n': n_total,
        'mb': peso_total / 1024**2,
        'segundos': dt,
    })
    log.info(f"  Imagenes: {n_total:,} | peso recortado total: "
             f"{peso_total/1024**2:.2f} MB | {dt:.1f}s")

log.info("=" * 92)
log.info(f"{'FUENTE':<42} {'ESC_M':>8} {'PX':>10} {'IMGS':>10} {'MB':>12} {'SEG':>6}")
log.info("-" * 92)
for r in resumen:
    log.info(f"{r['fuente']:<42} {r['escala']:>8.1f} {r['pixeles']:>10,} "
             f"{r['n']:>10,} {r['mb']:>12.2f} {r['segundos']:>6.1f}")
log.info("=" * 92)
log.info(f"TOTAL recortado a Cali 2021-{ANIO_FIN}: "
         f"{total_bytes/1024**2:,.2f} MB ({total_bytes/1024**3:.2f} GB)")
log.info("Nota: peso raw sin compresion. GeoTIFF/Zarr comprimidos pesaran ~2-5x menos.")
