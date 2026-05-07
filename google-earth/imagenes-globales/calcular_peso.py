import os
import sys
import ee
import time
from tqdm import tqdm

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))                  # google-earth/
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE))) # proyecto-3/

from config import PROJECT_ID, FUENTES, CALI  # type: ignore[reportMissingImports]
from logger import get_logger                  # type: ignore[reportMissingImports]

log = get_logger('calcular_peso')
ee.Initialize(project=PROJECT_ID)

ANIO_INICIO = 2021
ANIO_FIN = 2026  # exclusivo

region = ee.Geometry.Rectangle(CALI)

# Fuentes a ignorar (demasiado pesadas / ya sabemos su peso)
IGNORAR = {'COPERNICUS/S2_SR_HARMONIZED'}
fuentes = [f for f in FUENTES if f not in IGNORAR]

chunks = []
for anio in range(ANIO_INICIO, ANIO_FIN):
    for mes in range(1, 13):
        ini = f"{anio}-{mes:02d}-01"
        fin = f"{anio+1}-01-01" if mes == 12 else f"{anio}-{mes+1:02d}-01"
        chunks.append((ini, fin))

resumen = []
total_bytes = 0

log.info(f"Calculando peso de {len(fuentes)} fuentes x {len(chunks)} meses (filtrado a bbox Cali)")
if IGNORAR:
    log.info(f"Ignorando: {', '.join(sorted(IGNORAR))}")

for fuente in fuentes:
    log.info(f">>> {fuente}")
    t0 = time.time()
    n_total = 0
    peso_total = 0

    barra = tqdm(chunks, desc="  meses", unit="mes")
    for ini, fin in barra:
        col = (ee.ImageCollection(fuente)
               .filterBounds(region)
               .filterDate(ini, fin))

        stats = ee.Dictionary({
            'n': col.size(),
            'p': col.aggregate_sum('system:asset_size'),
        }).getInfo() or {}

        n_total += stats.get('n') or 0
        peso_total += stats.get('p') or 0

        barra.set_postfix({
            'imgs': n_total,
            'GB': f"{peso_total/1024**3:.1f}",
        })

    dt = time.time() - t0
    total_bytes += peso_total
    resumen.append({
        'fuente': fuente,
        'n': n_total,
        'gb': peso_total / 1024**3,
        'segundos': dt,
    })
    log.info(f"  Imagenes: {n_total:,} | peso (asset_size completo): "
             f"{peso_total/1024**3:.2f} GB | {dt:.1f}s")

log.info("=" * 78)
log.info(f"{'FUENTE':<42} {'IMGS':>10} {'GB':>12} {'SEG':>8}")
log.info("-" * 78)
for r in resumen:
    log.info(f"{r['fuente']:<42} {r['n']:>10,} {r['gb']:>12.2f} {r['segundos']:>8.1f}")
log.info("=" * 78)
log.info(f"TOTAL 2021-{ANIO_FIN}: {total_bytes/1024**3:,.2f} GB "
         f"({total_bytes/1024**4:.2f} TB)")
log.info("Nota: cifras = suma de 'system:asset_size' (peso del asset completo en GEE).")
log.info("Para S5P/ERA5/MODIS MAIAC los assets son globales; para S2 son tiles ~100km.")
log.info("El peso real de descarga recortado a Cali sera mucho menor (depende de res/bandas).")
