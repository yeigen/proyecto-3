import os
import sys
import io
import gc
import argparse
import itertools
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

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
import zarr as zr
from google.cloud import storage
from tqdm import tqdm
import gcsfs

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'google-earth'))

from config import PROJECT_ID, BANDAS_UTILES
from logger import get_logger

log = get_logger('zarr_modis')
FUENTE = 'MODIS/061/MCD19A2_GRANULES'
PREFIJO = FUENTE.replace('/', '_').lower()
BUCKET = 'fuentes-proyecto-3'
RAW_PREFIX = f'{PREFIJO}/raw'
ZARR_PREFIX = f'{PREFIJO}/panel.zarr'
DOWNLOAD_WORKERS = 4
bandas = BANDAS_UTILES[FUENTE]

cliente = storage.Client(project=PROJECT_ID)
bucket_gcs = cliente.bucket(BUCKET)


def agrupar_por_fecha(blobs):
    grupos = defaultdict(list)
    for b in blobs:
        fname = os.path.basename(b.name)
        if not fname.endswith('.tif'):
            continue
        parts = fname.replace('.tif', '').split('_')
        fecha = parts[1]
        grupos[fecha].append(b.name)
    return sorted(grupos.items(), key=lambda x: x[0])


def batched(iterable, n):
    it = iter(iterable)
    while True:
        chunk = list(itertools.islice(it, n))
        if not chunk:
            break
        yield chunk


def descargar_tif(blob_name):
    blob = bucket_gcs.blob(blob_name)
    buf = io.BytesIO(blob.download_as_bytes())
    return rioxarray.open_rasterio(buf).values.astype('float32')


def procesar_fecha(blob_names, H, W, n_bandas):
    acumulador = np.zeros((n_bandas, H, W), dtype='float64')
    contador = np.zeros((H, W), dtype='float32')

    for blob_name in blob_names:
        datos = descargar_tif(blob_name)
        if datos.ndim == 3:
            datos = datos[:n_bandas]
        elif datos.ndim == 2:
            datos = datos[np.newaxis, :n_bandas]

        mask = ~np.isnan(datos[0])
        contador += mask.astype('float32')
        for b in range(min(datos.shape[0], n_bandas)):
            acumulador[b][mask] += datos[b][mask]
        del datos

    valido = contador > 0
    resultado = np.full((n_bandas, H, W), np.nan, dtype='float32')
    for b in range(n_bandas):
        resultado[b][valido] = (acumulador[b][valido] / contador[valido]).astype('float32')

    return resultado


def procesar_lote(fechas_lote, H, W, n_bandas, blob_names_por_fecha):
    n = len(fechas_lote)
    cubo = np.empty((n, n_bandas, H, W), dtype='float32')
    img_ids = []

    for i, fecha in enumerate(fechas_lote):
        img_ids.append(fecha)
        blob_names = blob_names_por_fecha[fecha]
        cubo[i] = procesar_fecha(blob_names, H, W, n_bandas)

    ds = xr.Dataset(
        {'data': (('time', 'band', 'y', 'x'), cubo)},
        coords={
            'time': img_ids,
            'band': bandas,
            'y': y_vals_ref,
            'x': x_vals_ref,
        }
    )

    time_chunk = max(1, 256 * 1024**2 // (n_bandas * H * W * 4))
    ds = ds.chunk({
        'time': time_chunk,
        'band': n_bandas,
        'y': min(512, H),
        'x': min(512, W),
    })

    return ds


y_vals_ref = None
x_vals_ref = None


def main():
    global y_vals_ref, x_vals_ref

    p = argparse.ArgumentParser()
    p.add_argument('--max-fechas', type=int, default=None)
    p.add_argument('--batch-size', type=int, default=100)
    args = p.parse_args()

    blobs = sorted(bucket_gcs.list_blobs(prefix=f'{RAW_PREFIX}/'), key=lambda b: b.name)
    tifs = [b for b in blobs if b.name.endswith('.tif')]

    fechas_dict = agrupar_por_fecha(tifs)
    if args.max_fechas:
        fechas_dict = fechas_dict[:args.max_fechas]

    blob_names_por_fecha = {f: names for f, names in fechas_dict}
    fechas = [f for f, _ in fechas_dict]

    log.info(f'MODIS Zarr | {len(fechas)} fechas | {len(tifs)} TIFFs | {len(bandas)} bandas')
    log.info(f'destino: gs://{BUCKET}/{ZARR_PREFIX}/')
    log.info(f'batch_size={args.batch_size} | workers={DOWNLOAD_WORKERS}')

    primera_fecha = fechas[0]
    primer_tif = blob_names_por_fecha[primera_fecha][0]
    buf = io.BytesIO(bucket_gcs.blob(primer_tif).download_as_bytes())
    with rasterio.open(buf) as src:
        H, W = src.shape
        dx, dy = src.transform.a, src.transform.e
        xmin, ymax = src.transform.c, src.transform.f

    y_vals_ref = np.arange(ymax, ymax + H * dy, dy)[:H]
    x_vals_ref = np.arange(xmin, xmin + W * dx, dx)[:W]

    mem_por_fecha_mb = len(bandas) * H * W * 4 / 1024**2
    mem_por_batch_mb = args.batch_size * mem_por_fecha_mb
    log.info(f'Dimensiones: {H}x{W} | {mem_por_fecha_mb:.1f} MB/fecha | {mem_por_batch_mb:.0f} MB/batch')

    fs = gcsfs.GCSFileSystem(token='google_default')
    mapper = fs.get_mapper(f'{BUCKET}/{ZARR_PREFIX}')

    lotes = list(batched(fechas, args.batch_size))
    total_lotes = len(lotes)

    for batch_idx, lote in enumerate(lotes):
        log.info(f'Lote {batch_idx + 1}/{total_lotes}: {len(lote)} fechas')

        ds = procesar_lote(lote, H, W, len(bandas), blob_names_por_fecha)

        if batch_idx == 0:
            ds.to_zarr(mapper, mode='w', consolidated=False, zarr_format=2, compute=True)
        else:
            ds.to_zarr(mapper, mode='a', append_dim='time', consolidated=False, zarr_format=2, compute=True)

        del ds
        gc.collect()

        log.info(f'Lote {batch_idx + 1} escrito')

    log.info('Consolidando metadata...')
    zr.consolidate_metadata(mapper)

    peso_total = len(fechas) * len(bandas) * H * W * 4 / 1024**2
    log.info(f'Completado | {len(fechas)} fechas | {len(bandas)} bandas | {H}x{W} | {peso_total:.1f} MB raw')


if __name__ == '__main__':
    main()