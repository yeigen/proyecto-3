import os
import sys
import io
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

os.environ['CPL_LOG'] = '/dev/null'

import numpy as np
import xarray as xr
import rioxarray
from google.cloud import storage
from tqdm import tqdm

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'google-earth'))

from config import PROJECT_ID, BANDAS_UTILES
from logger import get_logger

log = get_logger('zarr_s5p_so2')
FUENTE = 'COPERNICUS/S5P/OFFL/L3_SO2'
PREFIJO = FUENTE.replace('/', '_').lower()
BUCKET = 'fuentes-proyecto-3'
RAW_PREFIX = f'{PREFIJO}/raw'
ZARR_PREFIX = f'{PREFIJO}/panel.zarr'
MAX_WORKERS = 16
bandas = BANDAS_UTILES[FUENTE]

cliente = storage.Client(project=PROJECT_ID)
bucket = cliente.bucket(BUCKET)


def leer_tif(blob):
    buf = io.BytesIO(blob.download_as_bytes())
    return rioxarray.open_rasterio(buf).values.astype('float32')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--max-imagenes', type=int, default=None)
    args = p.parse_args()

    blobs = sorted(bucket.list_blobs(prefix=f'{RAW_PREFIX}/'), key=lambda b: b.name)
    tifs = [b for b in blobs if b.name.endswith('.tif')]
    if args.max_imagenes:
        tifs = tifs[:args.max_imagenes]

    log.info(f'S5P SO2 Zarr | {len(tifs)} archivos | destino: gs://{BUCKET}/{ZARR_PREFIX}/')

    img_ids = [os.path.basename(b.name).replace('.tif', '') for b in tifs]

    buf = io.BytesIO(tifs[0].download_as_bytes())
    sample = rioxarray.open_rasterio(buf).isel(band=0)
    H, W = sample.shape

    cubo = np.zeros((len(tifs), len(bandas), H, W), dtype='float32')
    futuro_a_idx = {}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        for i, blob in enumerate(tifs):
            futuro_a_idx[ex.submit(leer_tif, blob)] = i

        with tqdm(total=len(tifs), desc='Leyendo', unit='img') as bar:
            for f in as_completed(futuro_a_idx):
                i = futuro_a_idx[f]
                cubo[i] = f.result()
                bar.update(1)

    coords = {
        'time': img_ids,
        'band': bandas,
        'y': sample.y.values,
        'x': sample.x.values,
    }

    ds = xr.Dataset({'data': (('time', 'band', 'y', 'x'), cubo)}, coords=coords)

    tmp = f'/tmp/s5p_so2_{len(tifs)}.zarr'
    ds.to_zarr(tmp, mode='w', consolidated=True, zarr_format=2)

    items = []
    for root, _, files in os.walk(tmp):
        for fname in files:
            local = os.path.join(root, fname)
            remote = f'{ZARR_PREFIX}/{os.path.relpath(local, tmp)}'
            items.append((local, remote))

    for local, remote in tqdm(items, desc='Subiendo', unit='file'):
        bucket.blob(remote).upload_from_filename(local)

    peso = cubo.nbytes / 1024**2
    log.info(f'Completado | {len(tifs)} timestamps | {len(bandas)} bandas | {peso:.1f} MB raw')


if __name__ == '__main__':
    main()
