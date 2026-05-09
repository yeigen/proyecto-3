import os
import sys
import io
import argparse
from collections import defaultdict

os.environ['CPL_LOG'] = '/dev/null'

import numpy as np
import xarray as xr
import dask.array as darr
from dask import delayed
from google.cloud import storage
from tqdm import tqdm

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'google-earth'))

from config import PROJECT_ID, BANDAS_UTILES
from logger import get_logger

log = get_logger('zarr_s2')
FUENTE = 'COPERNICUS/S2_SR_HARMONIZED'
PREFIJO = FUENTE.replace('/', '_').lower()
BUCKET_NAME = 'fuentes-proyecto-3'
RAW_PREFIX = f'{PREFIJO}/raw'
ZARR_PREFIX = f'{PREFIJO}/panel.zarr'
bandas = BANDAS_UTILES[FUENTE]

cliente = storage.Client(project=PROJECT_ID)
bucket = cliente.bucket(BUCKET_NAME)


def agrupar(blobs, max_imagenes=None):
    grupos = defaultdict(dict)
    for b in blobs:
        fname = os.path.basename(b.name)
        img_id, resto = fname.split('__', 1)
        tipo = resto.replace('.tif', '')
        grupos[img_id][tipo] = b.name
    items = [(i, g) for i, g in grupos.items() if 'spectral' in g and 'scl' in g]
    items = sorted(items, key=lambda x: x[0])
    if max_imagenes:
        items = items[:max_imagenes]
    return items


def info_sample(primer_grupo):
    _, files = primer_grupo
    buf = io.BytesIO(bucket.blob(files['spectral']).download_as_bytes(start=0, end=16384))
    import rasterio
    with rasterio.open(buf) as src:
        return src.shape, src.transform[5], src.transform[0], src.transform[2], src.transform[3]


@delayed
def leer_imagen(files_dict, shape_2d):
    import io
    import rioxarray
    import numpy as np
    from google.cloud import storage
    cliente_d = storage.Client(project='proyecto-analitica-3-495618')
    bucket_d = cliente_d.bucket('fuentes-proyecto-3')
    H, W = shape_2d

    buf = io.BytesIO(bucket_d.blob(files_dict['spectral']).download_as_bytes())
    da = rioxarray.open_rasterio(buf)
    spectral = da.values.astype('float32')

    buf = io.BytesIO(bucket_d.blob(files_dict['scl']).download_as_bytes())
    da = rioxarray.open_rasterio(buf)
    scl = da.values.astype('float32')

    return np.concatenate([spectral, scl], axis=0)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--max-imagenes', type=int, default=None)
    args = p.parse_args()

    blobs = sorted(bucket.list_blobs(prefix=f'{RAW_PREFIX}/'), key=lambda b: b.name)
    tifs = [b for b in blobs if '__' in b.name and b.name.endswith('.tif')]
    grupos = agrupar(tifs, max_imagenes=args.max_imagenes)

    log.info(f'S2 Zarr | {len(grupos)} imagenes | {len(bandas)} bandas | destino: gs://{BUCKET_NAME}/{ZARR_PREFIX}/')

    (H, W), dy, dx, xmin, ymax = info_sample(grupos[0])
    y_vals = np.arange(ymax, ymax + H * dy, dy)[:H]
    x_vals = np.arange(xmin, xmin + W * dx, dx)[:W]

    tareas = [leer_imagen(files, (H, W)) for _, files in grupos]
    arrays = [darr.from_delayed(t, shape=(len(bandas), H, W), dtype='float32') for t in tareas]
    cubo = darr.stack(arrays, axis=0)

    coords = {
        'time': [img_id for img_id, _ in grupos],
        'band': bandas,
        'y': y_vals,
        'x': x_vals,
    }

    ds = xr.Dataset({'data': (('time', 'band', 'y', 'x'), cubo)}, coords=coords)

    time_chunk = max(1, 256 * 1024**2 // (len(bandas) * H * W * 4))
    ds = ds.chunk({'time': time_chunk, 'band': len(bandas), 'y': min(512, H), 'x': min(512, W)})

    tmp = f'/tmp/s2_{len(grupos)}.zarr'
    log.info(f'Chunks: time={time_chunk} y={min(512,H)} x={min(512,W)}')
    ds.to_zarr(tmp, mode='w', consolidated=True, zarr_format=2)

    items = []
    for root, _, files in os.walk(tmp):
        for fname in files:
            local = os.path.join(root, fname)
            remote = f'{ZARR_PREFIX}/{os.path.relpath(local, tmp)}'
            items.append((local, remote))

    for local, remote in tqdm(items, desc='Subiendo', unit='file'):
        bucket.blob(remote).upload_from_filename(local)

    log.info(f'Completado | {len(grupos)} timestamps | {len(bandas)} bandas | {H}x{W}')


if __name__ == '__main__':
    main()
