"""
Reconstruye el Zarr MODIS final aplicando:
  - filtro del tile MODIS h10v08, que cubre Cali
  - máscara de _FillValue = -28672 antes de promediar
  - scale_factor = 0.001 a las bandas físicas (Optical_Depth_047/055, Column_WV)
  - AOD_QA como bitmask sin escalar

Fuente oficial: https://ladsweb.modaps.eosdis.nasa.gov/filespec/MODIS/6/MCD19A2

Lee los TIFFs raw de GCS y escribe `panel_v3.zarr`.
El nombre del archivo conserva `v2` por historial del fix, pero la salida vigente es v3.

Uso:
    python modis_v2_a_zarr.py
    python modis_v2_a_zarr.py --max-fechas 50
    python modis_v2_a_zarr.py --batch-size 50
"""
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

log = get_logger('zarr_modis_v2')

FUENTE = 'MODIS/061/MCD19A2_GRANULES'
PREFIJO = FUENTE.replace('/', '_').lower()
BUCKET = 'fuentes-proyecto-3'
RAW_PREFIX = f'{PREFIJO}/raw'
ZARR_PREFIX = f'{PREFIJO}/panel_v3.zarr'

MODIS_FILL = -28672
MODIS_SCALE = 0.001
BANDAS_FISICAS = {'Optical_Depth_047', 'Optical_Depth_055', 'Column_WV'}
DOWNLOAD_WORKERS = 16

bandas = BANDAS_UTILES[FUENTE]
indices_fisicas = [i for i, b in enumerate(bandas) if b in BANDAS_FISICAS]
indices_qa = [i for i, b in enumerate(bandas) if b not in BANDAS_FISICAS]

cliente = storage.Client(project=PROJECT_ID)
bucket_gcs = cliente.bucket(BUCKET)


TILE_MODIS_CALI = 'h10v08'


def agrupar_por_fecha(blobs):
    """Agrupa TIFFs por fecha, descartando gránulos MODIS que no cubren Cali.

    El export GEE de MCD19A2 bajó gránulos de TODO el cinturón ecuatorial
    (h10..h20 v17/v08); solo h10v08 cubre Cali. Los demás vienen como uint8
    con valores 0 (no aplican -28672 fill porque uint8 no representa el rango),
    y al promediarlos contaminan diluyendo el mean hacia 0. Filtramos por nombre.
    """
    grupos = defaultdict(list)
    descartados = 0
    for b in blobs:
        fname = os.path.basename(b.name)
        if not fname.endswith('.tif'):
            continue
        if TILE_MODIS_CALI not in fname:
            descartados += 1
            continue
        parts = fname.replace('.tif', '').split('_')
        fecha = parts[1]
        grupos[fecha].append(b.name)
    log.info(f'Filtro tile {TILE_MODIS_CALI}: descartados {descartados} TIFFs no-Cali')
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
    return rioxarray.open_rasterio(buf).values


def procesar_fecha(blob_names, H, W, n_bandas):
    """
    Promedia múltiples gránulos del mismo día:
      - bandas físicas: enmascara _FillValue=-28672 y NaN antes del promedio, luego × 0.001
      - AOD_QA (bitmask): toma el primer valor válido sin promediar (no tiene sentido promediar bits)
    Descargas en paralelo con ThreadPoolExecutor (DOWNLOAD_WORKERS); procesamiento numpy serial.
    """
    acumulador_fis = np.zeros((len(indices_fisicas), H, W), dtype='float64')
    contador_fis = np.zeros((len(indices_fisicas), H, W), dtype='float32')

    primer_qa = None

    with ThreadPoolExecutor(max_workers=DOWNLOAD_WORKERS) as ex:
        descargas = list(ex.map(descargar_tif, blob_names))

    for datos_raw in descargas:
        if datos_raw.ndim == 2:
            datos_raw = datos_raw[np.newaxis, ...]
        datos_raw = datos_raw[:n_bandas].astype('int32')

        for i_local, i_global in enumerate(indices_fisicas):
            banda = datos_raw[i_global]
            mask = np.isfinite(banda) & (banda != MODIS_FILL)
            contador_fis[i_local][mask] += 1
            acumulador_fis[i_local][mask] += banda[mask]

        if primer_qa is None and indices_qa:
            qa = datos_raw[indices_qa[0]]
            primer_qa = qa.astype('float32')
            primer_qa[~np.isfinite(primer_qa)] = np.nan

        del datos_raw

    del descargas
    resultado = np.full((n_bandas, H, W), np.nan, dtype='float32')

    for i_local, i_global in enumerate(indices_fisicas):
        valido = contador_fis[i_local] > 0
        media_raw = np.where(valido, acumulador_fis[i_local] / contador_fis[i_local], np.nan)
        resultado[i_global] = (media_raw * MODIS_SCALE).astype('float32')

    if primer_qa is not None and indices_qa:
        resultado[indices_qa[0]] = primer_qa

    return resultado


def procesar_lote(fechas_lote, H, W, n_bandas, blob_names_por_fecha):
    n = len(fechas_lote)
    cubo = np.empty((n, n_bandas, H, W), dtype='float32')
    img_ids = []

    for i, fecha in enumerate(tqdm(fechas_lote, desc='  fechas', leave=False)):
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

    ds['data'].attrs.update({
        'scale_factor_aplicado': MODIS_SCALE,
        'fill_value_origen': MODIS_FILL,
        'bandas_escaladas': sorted(BANDAS_FISICAS),
        'fuente': 'MCD19A2 v6.1 LAADS DAAC (https://ladsweb.modaps.eosdis.nasa.gov/filespec/MODIS/6/MCD19A2)',
        'fix_aplicado': 'mask(neq -28672) AND nan ANTES de promediar; multiply 0.001 DESPUES (bandas fisicas). AOD_QA sin escalar.',
    })

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
    p.add_argument('--validar-solo', action='store_true',
                   help='Solo lee 5 fechas y muestra estadísticas para validar fix, no escribe Zarr.')
    args = p.parse_args()

    blobs = sorted(bucket_gcs.list_blobs(prefix=f'{RAW_PREFIX}/'), key=lambda b: b.name)
    tifs = [b for b in blobs if b.name.endswith('.tif')]

    if not tifs:
        log.error(f'No se encontraron TIFFs en gs://{BUCKET}/{RAW_PREFIX}/')
        sys.exit(1)

    fechas_dict = agrupar_por_fecha(tifs)
    if args.max_fechas:
        fechas_dict = fechas_dict[:args.max_fechas]

    blob_names_por_fecha = {f: names for f, names in fechas_dict}
    fechas = [f for f, _ in fechas_dict]

    log.info(f'MODIS Zarr v3 | {len(fechas)} fechas | {len(tifs)} TIFFs raw | {len(bandas)} bandas')
    log.info(f'destino: gs://{BUCKET}/{ZARR_PREFIX}/')
    log.info(f'FIX aplicado: tile {TILE_MODIS_CALI} + mask(!= {MODIS_FILL}) antes de promediar + scale {MODIS_SCALE} en {sorted(BANDAS_FISICAS)}')

    primera_fecha = fechas[0]
    primer_tif = blob_names_por_fecha[primera_fecha][0]
    buf = io.BytesIO(bucket_gcs.blob(primer_tif).download_as_bytes())
    with rasterio.open(buf) as src:
        H, W = src.shape
        dx, dy = src.transform.a, src.transform.e
        xmin, ymax = src.transform.c, src.transform.f

    y_vals_ref = np.arange(ymax, ymax + H * dy, dy)[:H]
    x_vals_ref = np.arange(xmin, xmin + W * dx, dx)[:W]

    log.info(f'Dimensiones: H={H} W={W} | bandas {bandas}')

    if args.validar_solo:
        log.info('=== MODO VALIDACION (5 fechas) ===')

        log.info('\n--- DIAGNÓSTICO RAW del primer TIFF (sin scale, sin mask) ---')
        primer_blob = blob_names_por_fecha[fechas[0]][0]
        log.info(f'Blob: {primer_blob}')
        raw = descargar_tif(primer_blob)
        log.info(f'  dtype TIFF leído : {raw.dtype}')
        log.info(f'  shape TIFF leído : {raw.shape}')
        if raw.ndim == 2:
            raw = raw[np.newaxis, ...]
        for j in range(min(raw.shape[0], len(bandas))):
            banda = bandas[j] if j < len(bandas) else f'banda_{j}'
            v_raw = raw[j].flatten()
            v_no_fill = v_raw[v_raw != MODIS_FILL]
            v_finitos = v_no_fill[np.isfinite(v_no_fill)]
            n_fill = int((v_raw == MODIS_FILL).sum())
            n_nan = int((~np.isfinite(v_raw)).sum())
            log.info(
                f'  [{j}] {banda}: dtype={raw[j].dtype} · n={len(v_raw):,} '
                f'· fill(-28672)={n_fill:,} · nan={n_nan:,}'
            )
            if len(v_finitos) > 0:
                log.info(
                    f'      RAW (sin scale): min={v_finitos.min():.4f} · '
                    f'mediana={np.median(v_finitos):.4f} · max={v_finitos.max():.4f}'
                )

        log.info('\n--- ESCENARIO 1: aplicar × 0.001 ---')
        for j in range(min(raw.shape[0], len(bandas))):
            banda = bandas[j] if j < len(bandas) else f'banda_{j}'
            if banda not in BANDAS_FISICAS:
                continue
            v = raw[j].astype('float32')
            v_validos = v[(v != MODIS_FILL) & np.isfinite(v)] * MODIS_SCALE
            if len(v_validos) > 0:
                log.info(
                    f'  {banda} × 0.001: min={v_validos.min():.4f} · '
                    f'mediana={np.median(v_validos):.4f} · max={v_validos.max():.4f}'
                )

        log.info('\n--- ESCENARIO 2: sin aplicar × 0.001 (asumiendo GEE ya escaló) ---')
        for j in range(min(raw.shape[0], len(bandas))):
            banda = bandas[j] if j < len(bandas) else f'banda_{j}'
            if banda not in BANDAS_FISICAS:
                continue
            v = raw[j].astype('float32')
            v_validos = v[(v != MODIS_FILL) & np.isfinite(v)]
            if len(v_validos) > 0:
                log.info(
                    f'  {banda} sin scale: min={v_validos.min():.4f} · '
                    f'mediana={np.median(v_validos):.4f} · max={v_validos.max():.4f}'
                )

        log.info('\n--- AGREGACIÓN ACTUAL (5 fechas con × 0.001) ---')
        cubo = np.empty((5, len(bandas), H, W), dtype='float32')
        for i, fecha in enumerate(fechas[:5]):
            cubo[i] = procesar_fecha(blob_names_por_fecha[fecha], H, W, len(bandas))

        for j, banda in enumerate(bandas):
            v = cubo[:, j].flatten()
            v = v[np.isfinite(v)]
            if len(v) == 0:
                log.info(f'  {banda}: sin valores válidos')
                continue
            es_fisica = banda in BANDAS_FISICAS
            log.info(
                f'  {banda} ({"FÍSICA × scale" if es_fisica else "QA"}): '
                f'n={len(v):,} | min={v.min():.4f} | mediana={np.median(v):.4f} | max={v.max():.4f}'
            )

        log.info('\n=== DECISIÓN ===')
        log.info('  Si ESCENARIO 1 da rango ~[0, 0.004]    → GEE YA escaló los TIFFs (NO multiplicar × 0.001)')
        log.info('  Si ESCENARIO 1 da rango ~[0, 4.0]      → TIFFs son raw int16 (SI multiplicar × 0.001)')
        log.info('  Si ESCENARIO 2 da rango ~[0, 4.0]      → confirma escenario "ya escalado", quitar × 0.001')
        return

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
