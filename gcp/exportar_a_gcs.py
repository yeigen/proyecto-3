"""
Exporta imagenes GEE directo a Google Cloud Storage (sin disco local).
Usa streaming: getDownloadURL() -> GCS bucket via google-cloud-storage.

Uso:
  uv run python gcp/exportar_a_gcs.py --fuente 0 --dry-run
  uv run python gcp/exportar_a_gcs.py --fuente 3 --max-imagenes 2
"""

import os
import sys
import io
import time
import argparse
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from google.cloud import storage
from tqdm import tqdm
import ee

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'google-earth'))

from logger import get_logger  # type: ignore[reportMissingImports]
from config import (  # type: ignore[reportMissingImports]
    PROJECT_ID, CALI, FUENTES, DISPONIBILIDAD,
    ESCALA_OVERRIDE, BANDAS_UTILES,
)

log = get_logger('exportar_a_gcs')

BUCKET_NAME = 'fuentes-proyecto-3'
MAX_WORKERS = 8

ee.Initialize(project=PROJECT_ID)
region = ee.Geometry.Rectangle(CALI)
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET_NAME)


def banda_a_gcs(fuente_id, img_id, banda, escala_m):
    """Descarga una banda de GEE y la streamea directo a GCS."""
    blob_path = (f"{fuente_id.replace('/', '_').lower()}/"
                 f"raw/{img_id}__{banda}.tif")
    blob = bucket.blob(blob_path)

    if blob.exists():
        return img_id, banda, True, '(cache)'

    imagen = ee.Image(f"{fuente_id}/{img_id}").select(banda).clip(region)
    url = imagen.getDownloadURL({
        'region': region,
        'scale': escala_m,
        'crs': 'EPSG:4326',
        'format': 'GEO_TIFF',
    })

    r = requests.get(url, timeout=600, stream=True)
    r.raise_for_status()

    blob.upload_from_file(io.BytesIO(r.content), content_type='image/tiff')
    size_mb = blob.size / 1024**2
    return img_id, banda, True, f'{size_mb:.1f}MB'


def exportar_fuente(fuente_id, max_imagenes=None, dry_run=False):
    """Exporta todas las imagenes de una fuente a GCS."""
    ini, fin = DISPONIBILIDAD[fuente_id]
    col = (ee.ImageCollection(fuente_id)
           .filterBounds(region)
           .filterDate(ini, fin))

    ids = col.aggregate_array('system:index').getInfo() or []
    if max_imagenes:
        ids = ids[:max_imagenes]

    primera = col.first()
    escala_nominal = primera.select(0).projection().nominalScale().getInfo()
    escala_m = ESCALA_OVERRIDE.get(fuente_id, escala_nominal)
    disponibles = primera.bandNames().getInfo() or []
    bandas = [b for b in BANDAS_UTILES.get(fuente_id, []) if b in disponibles]

    nombre = fuente_id.split('/')[-1]
    total_bytes = len(ids) * len(bandas) * 4 * 1024 * 512  # estimado rough

    log.info(f"══════ {nombre} ══════")
    log.info(f"  Imagenes: {len(ids):,} | bandas: {len(bandas)} "
             f"| escala: {escala_m:.0f}m | est: {total_bytes/1024**3:.1f}GB")
    log.info(f"  GCS: gs://{BUCKET_NAME}/{fuente_id.replace('/', '_').lower()}/")

    if dry_run:
        log.info("  [DRY RUN] sin descargar")
        return

    tareas = [(fuente_id, i, b, escala_m) for i in ids for b in bandas]
    ok = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futuros = [ex.submit(banda_a_gcs, *t) for t in tareas]
        with tqdm(total=len(tareas), desc=f'  {nombre}', unit='b') as pbar:
            for f in as_completed(futuros):
                _, _, success, info = f.result()
                if success:
                    ok += 1
                pbar.update(1)

    log.info(f"  Completado: {ok}/{len(tareas)} bandas")


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--fuente', type=int, default=None,
                   help='Indice en FUENTES (-1 para todas)')
    p.add_argument('--max-imagenes', type=int, default=None,
                   help='Limite de imagenes por fuente')
    p.add_argument('--dry-run', action='store_true',
                   help='Solo mostrar info, no descargar')
    args = p.parse_args()

    fuentes = FUENTES if args.fuente is None or args.fuente < 0 else [FUENTES[args.fuente]]

    for fuente_id in fuentes:
        exportar_fuente(fuente_id, max_imagenes=args.max_imagenes,
                        dry_run=args.dry_run)


if __name__ == '__main__':
    main()
