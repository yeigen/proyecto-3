"""
Exporta imagenes GEE a GCS: GeoTIFF multi-banda -> Zarr con Dask.

Pipeline:
  1. Descarga paralela de GeoTIFFs multi-banda (1 archivo por imagen)
  2. Conversion a Zarr con Dask (chunking espacio-temporal)
  3. Subida del Zarr a GCS
  4. (Opcional) limpieza de raw

Uso:
  uv run python gcp/exportar_zarr_gcs.py --fuente 5 --dry-run
  uv run python gcp/exportar_zarr_gcs.py --fuente 5
  uv run python gcp/exportar_zarr_gcs.py --fuente -1  # TODAS
"""

import os
import sys
import io
import time
import json
import hashlib
import argparse
import warnings
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

# Silenciar warnings cosmeticos de GDAL/rioxarray (multi-banda cientifico)
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', message='.*TIFFReadDirectory.*')
os.environ['CPL_LOG'] = '/dev/null'     # silencia errores GDAL
os.environ['GDAL_PAM_ENABLED'] = 'NO'   # no genera .aux.xml

import ee
import numpy as np
import xarray as xr
import rioxarray
from google.cloud import storage
from tqdm import tqdm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'google-earth'))

from logger import get_logger  # type: ignore[reportMissingImports]
from config import (  # type: ignore[reportMissingImports]
    PROJECT_ID, CALI, FUENTES, DISPONIBILIDAD,
    ESCALA_OVERRIDE, BANDAS_UTILES,
)

log = get_logger('exportar_zarr_gcs')
ee.Initialize(project=PROJECT_ID)

BUCKET_NAME = 'fuentes-proyecto-3'
MAX_WORKERS_DOWNLOAD = 8
BATCH_SIZE = 50  # imagenes por batch antes de convertir a Zarr

region = ee.Geometry.Rectangle(CALI)
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET_NAME)


def descargar_tif(fuente_id, img_id, bandas, escala_m):
    """Descarga una imagen multi-banda como GeoTIFF y la sube a GCS."""
    prefijo = fuente_id.replace('/', '_').lower()
    blob_path = f"{prefijo}/raw/{img_id}.tif"
    blob = bucket.blob(blob_path)

    if blob.exists():
        blob.reload()
        return img_id, True, '(cache)', blob.size

    imagen = ee.Image(f"{fuente_id}/{img_id}").select(bandas).clip(region)
    url = imagen.getDownloadURL({
        'region': region,
        'scale': escala_m,
        'crs': 'EPSG:4326',
        'format': 'GEO_TIFF',
    })
    r = requests.get(url, timeout=600)
    r.raise_for_status()

    blob.upload_from_file(io.BytesIO(r.content), content_type='image/tiff')
    return img_id, True, 'ok', blob.size


def descargar_lote(fuente_id, ids, bandas, escala_m):
    """Descarga paralela de un lote de imagenes multi-banda a GCS."""
    ok, fallas = 0, 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS_DOWNLOAD) as ex:
        futuros = {ex.submit(descargar_tif, fuente_id, i, bandas, escala_m): i
                   for i in ids}
        with tqdm(total=len(ids), desc='  descargando', unit='img') as pbar:
            for f in as_completed(futuros):
                iid, success, _, _ = f.result()
                if success:
                    ok += 1
                else:
                    fallas += 1
                pbar.update(1)
    return ok, fallas


def convertir_a_zarr(fuente_id, ids, bandas, zarr_name):
    """Lee GeoTIFFs de GCS, apila en Zarr con Dask, sube Zarr a GCS."""
    prefijo = fuente_id.replace('/', '_').lower()
    log.info(f"  Convirtiendo {len(ids)} imagenes a Zarr: {zarr_name}")

    # Bajar temporalmente para construir el Zarr
    import tempfile
    import shutil
    tmp = tempfile.mkdtemp(prefix='zarr_')
    raw_tmp = os.path.join(tmp, 'raw')
    zarr_tmp = os.path.join(tmp, 'zarr')
    os.makedirs(raw_tmp, exist_ok=True)

    datasets = []
    coords_time = []
    for img_id in tqdm(ids, desc='  bajando de GCS', unit='img'):
        blob_path = f"{prefijo}/raw/{img_id}.tif"
        blob = bucket.blob(blob_path)
        local = os.path.join(raw_tmp, f"{img_id}.tif")
        blob.download_to_filename(local)
        da = rioxarray.open_rasterio(local)
        if isinstance(da, list):
            da = da[0]
        datasets.append(da)
        coords_time.append(img_id)
        os.remove(local)

    # Concatenar en el eje temporal y guardar Zarr
    ds = xr.concat(datasets, dim='time')
    ds['time'] = coords_time

    chunk_time = max(1, min(50, len(ids)))
    ds = ds.chunk({'time': chunk_time, 'y': -1, 'x': -1})
    ds.to_zarr(zarr_tmp, mode='w', consolidated=True, zarr_format=2)

    # Subir Zarr a GCS
    log.info(f"  Subiendo Zarr a gs://{BUCKET_NAME}/{prefijo}/{zarr_name}/")
    for root, _, files in os.walk(zarr_tmp):
        for fname in files:
            local_path = os.path.join(root, fname)
            rel = os.path.relpath(local_path, zarr_tmp)
            blob = bucket.blob(f"{prefijo}/{zarr_name}/{rel}")
            blob.upload_from_filename(local_path)

    # Calcular hash y metadata
    total_bytes = sum(os.path.getsize(os.path.join(root, f))
                      for root, _, files in os.walk(zarr_tmp) for f in files)
    shutil.rmtree(tmp)
    return total_bytes


def exportar_fuente(fuente_id, max_imagenes=None, dry_run=False):
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
    prefijo = fuente_id.replace('/', '_').lower()
    log.info(f"══════ {nombre} ══════")
    log.info(f"  Imagenes: {len(ids):,} | bandas: {len(bandas)} ({bandas}) "
             f"| escala: {escala_m:.0f}m")
    log.info(f"  GCS: gs://{BUCKET_NAME}/{prefijo}/")

    if dry_run:
        log.info("  [DRY RUN]")
        return

    # Dividir en batches
    batches = [ids[i:i + BATCH_SIZE] for i in range(0, len(ids), BATCH_SIZE)]
    log.info(f"  Batches: {len(batches)} x ~{BATCH_SIZE} imagenes")

    manifest_entries = []
    total_raw_bytes = 0
    total_zarr_bytes = 0

    for n, batch_ids in enumerate(batches, 1):
        batch_name = f"batch_{n:04d}"
        log.info(f"  [{n}/{len(batches)}] {batch_name} ({len(batch_ids)} imgs)")

        # 1. Descargar GeoTIFFs multi-banda a GCS
        t0 = time.time()
        ok, fallas = descargar_lote(fuente_id, batch_ids, bandas, escala_m)
        dt = time.time() - t0

        # Calcular peso del batch raw
        batch_bytes = 0
        for i in batch_ids:
            b = bucket.get_blob(f"{prefijo}/raw/{i}.tif")
            if b is not None:
                batch_bytes += b.size or 0
        total_raw_bytes += batch_bytes
        log.info(f"    raw: {ok} ok, {fallas} fallas | "
                 f"{batch_bytes/1024**2:.0f}MB | {dt:.0f}s")

        # 2. Convertir a Zarr
        t0 = time.time()
        zarr_name = f"{batch_name}.zarr"
        zarr_bytes = convertir_a_zarr(fuente_id, batch_ids, bandas, zarr_name)
        total_zarr_bytes += zarr_bytes
        dt2 = time.time() - t0
        log.info(f"    zarr: {zarr_bytes/1024**2:.0f}MB | {dt2:.0f}s")

        # 3. Manifest entry
        for iid in batch_ids:
            manifest_entries.append({
                'fuente': fuente_id,
                'imagen_id': iid,
                'batch': batch_name,
                'zarr': f"gs://{BUCKET_NAME}/{prefijo}/{zarr_name}",
                'bandas': bandas,
            })

    # Guardar manifest
    manifest = {
        'fuente': fuente_id,
        'total_imagenes': len(ids),
        'total_bandas': len(bandas),
        'bandas': bandas,
        'escala_m': escala_m,
        'bbox': CALI,
        'rango_fechas': [ini, fin],
        'raw_bytes': total_raw_bytes,
        'zarr_bytes': total_zarr_bytes,
        'imagenes': manifest_entries,
    }
    manifest_blob = bucket.blob(f"{prefijo}/manifest.json")
    manifest_blob.upload_from_string(
        json.dumps(manifest, indent=2), content_type='application/json')
    log.info(f"  Manifest: gs://{BUCKET_NAME}/{prefijo}/manifest.json")
    log.info(f"  TOTAL raw: {total_raw_bytes/1024**3:.2f}GB | "
             f"zarr: {total_zarr_bytes/1024**3:.2f}GB")


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--fuente', type=int, default=None)
    p.add_argument('--max-imagenes', type=int, default=None)
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args()

    if args.fuente is not None and args.fuente >= 0:
        fuentes = [FUENTES[args.fuente]]
    else:
        fuentes = FUENTES

    for fuente_id in fuentes:
        exportar_fuente(fuente_id, max_imagenes=args.max_imagenes,
                        dry_run=args.dry_run)


if __name__ == '__main__':
    main()
