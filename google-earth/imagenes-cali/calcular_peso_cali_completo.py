import os
import sys
import time
import math
from datetime import date, timedelta
import ee
from tqdm import tqdm

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from config import (  # type: ignore[reportMissingImports]
    PROJECT_ID, FUENTES, CALI, DISPONIBILIDAD, ESCALA_OVERRIDE,
)
from logger import get_logger  # type: ignore[reportMissingImports]

log = get_logger('calcular_peso_cali_completo')
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


def chunks_mensuales(ini_str, fin_str):
    ini = date.fromisoformat(ini_str)
    fin = date.fromisoformat(fin_str)
    out = []
    cur = date(ini.year, ini.month, 1)
    while cur < fin:
        siguiente_mes = (cur.replace(day=28) + timedelta(days=4)).replace(day=1)
        out.append((max(cur, ini).isoformat(), min(siguiente_mes, fin).isoformat()))
        cur = siguiente_mes
    return out


def info_fuente(fuente, ini_str, fin_str):
    primera = (ee.ImageCollection(fuente)
               .filterBounds(region)
               .filterDate(ini_str, fin_str)
               .first())
    info = primera.getInfo()
    bandas = info.get('bands', [])
    escala_nativa = primera.select(0).projection().nominalScale().getInfo()
    bytes_px = sum(
        BYTES_DTYPE.get(b.get('data_type', {}).get('precision', ''), 4)
        for b in bandas
    )
    return escala_nativa, bytes_px, len(bandas)


resumen = []
total_bytes = 0

log.info(f"Estimando peso REAL recortado a Cali con rangos completos por dataset")

for fuente in FUENTES:
    ini_str, fin_str = DISPONIBILIDAD[fuente]
    log.info(f">>> {fuente}  [{ini_str} -> {fin_str}]")
    t0 = time.time()
    try:
        escala_nativa, bytes_px, n_bandas = info_fuente(fuente, ini_str, fin_str)
    except Exception as e:
        log.warning(f"  No se pudo obtener info: {e}")
        continue

    escala_m = ESCALA_OVERRIDE.get(fuente, escala_nativa)
    pixeles = math.ceil(ancho_m / escala_m) * math.ceil(alto_m / escala_m)
    peso_img = pixeles * bytes_px

    nota_escala = f"{escala_m:.2f} m/px"
    if fuente in ESCALA_OVERRIDE:
        nota_escala += f" (override; nativa nominalScale={escala_nativa:.2f})"
    log.info(f"  Resolucion: {nota_escala} | bandas: {n_bandas} "
             f"| pixeles bbox: {pixeles:,} | bytes/px: {bytes_px} "
             f"| peso/imagen: {peso_img/1024:.2f} KB")

    chunks = chunks_mensuales(ini_str, fin_str)
    n_total = 0
    barra = tqdm(chunks, desc='  meses', unit='mes')
    for ini, fin in barra:
        col = (ee.ImageCollection(fuente)
               .filterBounds(region)
               .filterDate(ini, fin))
        n = col.size().getInfo() or 0
        n_total += n
        barra.set_postfix({'imgs': n_total, 'GB': f"{n_total*peso_img/1024**3:.2f}"})

    peso_total = n_total * peso_img
    dt = time.time() - t0
    total_bytes += peso_total
    resumen.append({
        'fuente': fuente,
        'rango': f"{ini_str}->{fin_str}",
        'escala': escala_m,
        'pixeles': pixeles,
        'n': n_total,
        'gb': peso_total / 1024**3,
        'segundos': dt,
    })
    log.info(f"  Imagenes: {n_total:,} | peso recortado total: "
             f"{peso_total/1024**3:.2f} GB | {dt:.1f}s")

log.info("=" * 110)
log.info(f"{'FUENTE':<35} {'RANGO':<25} {'ESC_M':>8} {'PX':>10} {'IMGS':>10} {'GB':>10} {'SEG':>6}")
log.info("-" * 110)
for r in resumen:
    log.info(f"{r['fuente']:<35} {r['rango']:<25} {r['escala']:>8.1f} "
             f"{r['pixeles']:>10,} {r['n']:>10,} {r['gb']:>10.2f} {r['segundos']:>6.1f}")
log.info("=" * 110)
log.info(f"TOTAL recortado a Cali (rangos completos): "
         f"{total_bytes/1024**3:,.2f} GB ({total_bytes/1024**4:.2f} TB)")
log.info("Nota: peso raw sin compresion. GeoTIFF/Zarr comprimidos pesaran ~2-5x menos.")
log.info(f"Umbral del proyecto: 50 GB. {'CUMPLE' if total_bytes/1024**3 >= 50 else 'NO CUMPLE'}.")
