import os
import sys
import io
import argparse
from collections import defaultdict

if os.name == 'nt':
    os.environ['CPL_LOG'] = 'NUL'
else:
    os.environ['CPL_LOG'] = '/dev/null'

os.environ['GDAL_CACHEMAX'] = '64'
os.environ['GDAL_DISABLE_READDIR_ON_OPEN'] = 'TRUE'

import numpy as np
import xarray as xr
import rioxarray
import rasterio
from google.cloud import storage
from tqdm import tqdm
import dask
import dask.array as darr
import gcsfs

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'google-earth'))

from config import PROJECT_ID, BANDAS_UTILES
from logger import get_logger

log = get_logger('zarr_s2')
FUENTE = 'COPERNICUS/S2_SR_HARMONIZED'
PREFIJO = FUENTE.replace('/', '_').lower()
BUCKET = 'fuentes-proyecto-3'
RAW_PREFIX = f'{PREFIJO}/raw'
ZARR_PREFIX = f'{PREFIJO}/panel.zarr'
bandas = BANDAS_UTILES[FUENTE]

cliente = storage.Client(project=PROJECT_ID)
bucket = cliente.bucket(BUCKET)


def agrupar(blobs, max_imagenes=None):
    grupos = defaultdict(dict)
    for b in blobs:
        fname = os.path.basename(b.name)
        img_id, resto = fname.split('__', 1)
        tipo = resto.replace('.tif', '')
        grupos[img_id][tipo] = b.name
    items = [(i, g) for i, g in grupos.items() if all(b in g for b in bandas)]
    items = sorted(items, key=lambda x: x[0])
    if max_imagenes:
        items = items[:max_imagenes]
    return items


@dask.delayed(pure=True)
def leer_imagen(files_dict, H, W, bandas_list):
    arr = np.empty((len(bandas_list), H, W), dtype='float32')
    for i, banda in enumerate(bandas_list):
        blob = bucket.blob(files_dict[banda])
        buf = io.BytesIO(blob.download_as_bytes())
        data = rioxarray.open_rasterio(buf).values
        if data.ndim == 3:
            data = data[0]
        arr[i] = data.astype('float32')
    return arr


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--max-imagenes', type=int, default=None)
    args = p.parse_args()

    blobs = sorted(bucket.list_blobs(prefix=f'{RAW_PREFIX}/'), key=lambda b: b.name)
    tifs = [b for b in blobs if '__' in b.name and b.name.endswith('.tif')]
    grupos = agrupar(tifs, max_imagenes=args.max_imagenes)

    log.info(f'S2 Zarr | {len(grupos)} imagenes | {len(bandas)} bandas')
    log.info(f'destino: gs://{BUCKET}/{ZARR_PREFIX}/')

    (img_id_0, files_0) = grupos[0]
    buf = io.BytesIO(bucket.blob(files_0['B4']).download_as_bytes(start=0, end=16384))
    with rasterio.open(buf) as src:
        H, W = src.shape
        dx, dy = src.transform.a, src.transform.e
        xmin, ymax = src.transform.c, src.transform.f
    y_vals = np.arange(ymax, ymax + H * dy, dy)[:H]
    x_vals = np.arange(xmin, xmin + W * dx, dx)[:W]

    tareas = [leer_imagen(files, H, W, bandas) for _, files in grupos]

    arrays = [
        darr.from_delayed(t, shape=(len(bandas), H, W), dtype='float32')
        for t in tareas
    ]

    cubo = darr.stack(arrays, axis=0)

    coords = {
        'time': [img_id for img_id, _ in grupos],
        'band': bandas,
        'y': y_vals,
        'x': x_vals,
    }

    ds = xr.Dataset({'data': (('time', 'band', 'y', 'x'), cubo)}, coords=coords)

    time_chunk = max(1, 256 * 1024**2 // (len(bandas) * H * W * 4))
    ds = ds.chunk({
        'time': time_chunk,
        'band': len(bandas),
        'y': min(512, H),
        'x': min(512, W),
    })

    log.info(f'Shape: {cubo.shape} | time_chunk={time_chunk} | y_chunk={min(512,H)} | x_chunk={min(512,W)}')

    fs = gcsfs.GCSFileSystem(token='google_default')
    mapper = fs.get_mapper(f'{BUCKET}/{ZARR_PREFIX}')

    with dask.config.set(scheduler='threads', num_workers=2):
        ds.to_zarr(mapper, mode='w', consolidated=True, zarr_format=2, compute=True)

    peso_total = len(grupos) * len(bandas) * H * W * 4 / 1024**3
    log.info(f'Completado | {len(grupos)} timestamps | {len(bandas)} bandas | {H}x{W} | {peso_total:.1f} GB raw')


if __name__ == '__main__':
    main()
