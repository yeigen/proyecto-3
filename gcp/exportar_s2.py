import os
import sys
import io
import argparse
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

import ee
from google.cloud import storage
from tqdm import tqdm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'google-earth'))

from config import PROJECT_ID, CALI, BANDAS_UTILES, DISPONIBILIDAD, ESCALA_OVERRIDE
from logger import get_logger

log = get_logger('exportar_s2')
FUENTE = 'COPERNICUS/S2_SR_HARMONIZED'
PREFIJO = FUENTE.replace('/', '_').lower()
BUCKET = 'fuentes-proyecto-3'
MAX_WORKERS = 8
ESCALA = ESCALA_OVERRIDE[FUENTE]

ee.Initialize(project=PROJECT_ID)
region = ee.Geometry.Rectangle(CALI)
cliente = storage.Client(project=PROJECT_ID)
bucket = cliente.bucket(BUCKET)

ini, fin = DISPONIBILIDAD[FUENTE]
bandas = BANDAS_UTILES[FUENTE]


def exportar_banda(fuente_id, img_id, banda):
    path = f'{PREFIJO}/raw/{img_id}__{banda}.tif'
    blob = bucket.blob(path)
    if blob.exists():
        return img_id, banda, True, '(cache)'

    imagen = ee.Image(f'{fuente_id}/{img_id}').select(banda).clip(region)
    url = imagen.getDownloadURL({
        'region': region,
        'scale': ESCALA,
        'crs': 'EPSG:4326',
        'format': 'GEO_TIFF',
    })
    r = requests.get(url, timeout=300, stream=True)
    r.raise_for_status()
    blob.upload_from_file(io.BytesIO(r.content), content_type='image/tiff')
    return img_id, banda, True, f'{blob.size / 1024**2:.1f}MB'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--max-imagenes', type=int, default=None)
    args = p.parse_args()

    ids = (
        ee.ImageCollection(FUENTE)
        .filterBounds(region)
        .filterDate(ini, fin)
        .aggregate_array('system:index')
        .getInfo()
    ) or []

    if args.max_imagenes:
        ids = ids[:args.max_imagenes]

    tareas = [(FUENTE, i, b) for i in ids for b in bandas]
    log.info(f'S2 | {len(ids)} imagenes x {len(bandas)} bandas = {len(tareas)} archivos | escala: {ESCALA}m')
    log.info(f'gs://{BUCKET}/{PREFIJO}/raw/')

    if args.dry_run:
        log.info('[DRY RUN] — sin descargar')
        return

    ok = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futuros = [ex.submit(exportar_banda, *t) for t in tareas]
        with tqdm(total=len(tareas), desc='S2', unit='banda') as bar:
            for f in as_completed(futuros):
                _, banda, success, info = f.result()
                if success:
                    ok += 1
                bar.set_postfix_str(f'{banda} {info}')
                bar.update(1)

    log.info(f'Completado: {ok}/{len(tareas)} bandas')


if __name__ == '__main__':
    main()
