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

from config import PROJECT_ID, CALI, BANDAS_UTILES, DISPONIBILIDAD
from logger import get_logger

log = get_logger('exportar_modis')
FUENTE = 'MODIS/061/MCD19A2_GRANULES'
PREFIJO = FUENTE.replace('/', '_').lower()
BUCKET = 'fuentes-proyecto-3'
MAX_WORKERS = 8
ESCALA = 927

ee.Initialize(project=PROJECT_ID)
region = ee.Geometry.Rectangle(CALI)
cliente = storage.Client(project=PROJECT_ID)
bucket = cliente.bucket(BUCKET)

ini, fin = DISPONIBILIDAD[FUENTE]
bandas = BANDAS_UTILES[FUENTE]


def exportar(img_id, dry_run):
    path = f'{PREFIJO}/raw/{img_id}.tif'
    blob = bucket.blob(path)
    if blob.exists():
        return img_id, '(cache)'
    if dry_run:
        return img_id, '(dry)'

    imagen = ee.Image(f'{FUENTE}/{img_id}').select(bandas).clip(region)
    url = imagen.getDownloadURL({
        'region': region,
        'scale': ESCALA,
        'crs': 'EPSG:4326',
        'format': 'GEO_TIFF',
    })
    r = requests.get(url, timeout=300, stream=True)
    r.raise_for_status()
    blob.upload_from_file(io.BytesIO(r.content), content_type='image/tiff')
    return img_id, f'{blob.size / 1024:.1f}KB'


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

    log.info(f'MODIS | {len(ids)} imagenes | bandas: {bandas} | escala: {ESCALA}m')
    log.info(f'gs://{BUCKET}/{PREFIJO}/raw/')

    if args.dry_run:
        log.info('[DRY RUN] — sin descargar')
        return

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futuros = [ex.submit(exportar, i, args.dry_run) for i in ids]
        with tqdm(total=len(ids), desc='MODIS', unit='img') as bar:
            for f in as_completed(futuros):
                img_id, info = f.result()
                bar.set_postfix_str(f'{img_id[:24]} {info}')
                bar.update(1)

    log.info(f'Completado: {len(ids)} imagenes')


if __name__ == '__main__':
    main()
