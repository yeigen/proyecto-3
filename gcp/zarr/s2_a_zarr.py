import os
import sys
import io
import gc
import argparse
import itertools
from concurrent.futures import ThreadPoolExecutor, as_completed

if os.name == 'nt':
    os.environ['CPL_LOG'] = 'NUL'
else:
    os.environ['CPL_LOG'] = '/dev/null'

os.environ['GDAL_CACHEMAX'] = '64'
os.environ['GDAL_DISABLE_READDIR_ON_OPEN'] = 'TRUE'

import numpy as np
import numcodecs
import xarray as xr
import rioxarray
import rasterio
import zarr as zr
from google.cloud import storage
from tqdm import tqdm
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
DOWNLOAD_WORKERS = 2
bandas = BANDAS_UTILES[FUENTE]

TIME_CHUNK = 5
Y_CHUNK = 974
X_CHUNK = 974
BAND_CHUNK = len(bandas)

COMPRESSOR = numcodecs.Blosc(cname='zstd', clevel=5, shuffle=numcodecs.Blosc.BITSHUFFLE)

cliente = storage.Client(project=PROJECT_ID)
bucket_gcs = cliente.bucket(BUCKET)


def agrupar(blobs, max_imagenes=None):
    from collections import defaultdict
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


def batched(iterable, n):
    it = iter(iterable)
    while True:
        chunk = list(itertools.islice(it, n))
        if not chunk:
            break
        yield chunk


def descargar_banda(blob_name):
    blob = bucket_gcs.blob(blob_name)
    buf = io.BytesIO(blob.download_as_bytes())
    data = rioxarray.open_rasterio(buf).values
    if data.ndim == 3:
        data = data[0]
    return data.astype('float32')


def procesar_lote(grupos_lote, H, W, bandas, y_vals, x_vals):
    n = len(grupos_lote)
    cubo = np.empty((n, len(bandas), H, W), dtype='float32')
    img_ids = []

    for img_idx, (img_id, files_dict) in enumerate(grupos_lote):
        img_ids.append(img_id)
        with ThreadPoolExecutor(max_workers=DOWNLOAD_WORKERS) as ex:
            futuros = {}
            for banda_idx, banda in enumerate(bandas):
                futuros[ex.submit(descargar_banda, files_dict[banda])] = banda_idx

            for f in as_completed(futuros):
                banda_idx = futuros[f]
                cubo[img_idx, banda_idx] = f.result()

    ds = xr.Dataset(
        {'data': (('time', 'band', 'y', 'x'), cubo)},
        coords={
            'time': img_ids,
            'band': bandas,
            'y': y_vals,
            'x': x_vals,
        }
    )

    ds = ds.chunk({
        'time': TIME_CHUNK,
        'band': BAND_CHUNK,
        'y': Y_CHUNK,
        'x': X_CHUNK,
    })

    return ds


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--max-imagenes', type=int, default=None)
    p.add_argument('--batch-size', type=int, default=TIME_CHUNK)
    args = p.parse_args()

    blobs = sorted(bucket_gcs.list_blobs(prefix=f'{RAW_PREFIX}/'), key=lambda b: b.name)
    tifs = [b for b in blobs if '__' in b.name and b.name.endswith('.tif')]
    grupos = agrupar(tifs, max_imagenes=args.max_imagenes)

    mem_por_batch_gb = args.batch_size * len(bandas) * 3897 * 3897 * 4 / 1024**3
    chunk_size_mb = TIME_CHUNK * BAND_CHUNK * Y_CHUNK * X_CHUNK * 4 / 1024**2
    n_time_chunks = -(-len(grupos) // TIME_CHUNK)
    n_spatial_chunks = -(-3897 // Y_CHUNK) * (-(-3897 // X_CHUNK))
    total_data_chunks = n_time_chunks * n_spatial_chunks

    log.info(f'S2 Zarr | {len(grupos)} imagenes | {len(bandas)} bandas')
    log.info(f'destino: gs://{BUCKET}/{ZARR_PREFIX}/')
    log.info(f'batch_size={args.batch_size} | ~{mem_por_batch_gb:.1f} GB/batch | workers={DOWNLOAD_WORKERS}')
    log.info(f'chunks=({TIME_CHUNK},{BAND_CHUNK},{Y_CHUNK},{X_CHUNK}) | {chunk_size_mb:.0f} MB/chunk | ~{total_data_chunks} data chunks')
    log.info(f'compresion: blosc/zstd/c5/bitshuffle')

    (img_id_0, files_0) = grupos[0]
    buf = io.BytesIO(bucket_gcs.blob(files_0['B4']).download_as_bytes(start=0, end=16384))
    with rasterio.open(buf) as src:
        H, W = src.shape
        dx, dy = src.transform.a, src.transform.e
        xmin, ymax = src.transform.c, src.transform.f
    y_vals = np.arange(ymax, ymax + H * dy, dy)[:H]
    x_vals = np.arange(xmin, xmin + W * dx, dx)[:W]

    log.info(f'Dimensiones: {H}x{W}')

    fs = gcsfs.GCSFileSystem(token='google_default')
    mapper = fs.get_mapper(f'{BUCKET}/{ZARR_PREFIX}')

    lotes = list(batched(grupos, args.batch_size))
    total_lotes = len(lotes)

    encoding = {
        'data': {
            'chunks': (TIME_CHUNK, BAND_CHUNK, Y_CHUNK, X_CHUNK),
            'compressor': COMPRESSOR,
            'dtype': 'float32',
            '_FillValue': np.nan,
        }
    }

    for batch_idx, lote in enumerate(lotes):
        log.info(f'Lote {batch_idx + 1}/{total_lotes}: {len(lote)} timestamps')

        ds = procesar_lote(lote, H, W, bandas, y_vals, x_vals)

        if batch_idx == 0:
            ds.to_zarr(mapper, mode='w', consolidated=False, zarr_format=2,
                       encoding=encoding, compute=True)
        else:
            ds.to_zarr(mapper, mode='a', append_dim='time', consolidated=False,
                       zarr_format=2, compute=True)

        del ds
        gc.collect()

        log.info(f'Lote {batch_idx + 1} escrito')

    log.info('Consolidando metadata...')
    zr.consolidate_metadata(mapper)

    peso_total = len(grupos) * len(bandas) * H * W * 4 / 1024**3
    log.info(f'Completado | {len(grupos)} timestamps | {len(bandas)} bandas | {H}x{W} | {peso_total:.1f} GB raw')
    log.info(f'Chunks finales: ({TIME_CHUNK},{BAND_CHUNK},{Y_CHUNK},{X_CHUNK})')
    log.info(f'Tamano estimado zarr: ~50-60 GB con zstd bitshuffle')


if __name__ == '__main__':
    main()