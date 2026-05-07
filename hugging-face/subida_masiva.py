import os
import sys
import json
import math
import time
import shutil
import logging
import argparse
import warnings
import requests

warnings.filterwarnings('ignore', message='It seems you are trying to upload a large folder')
import ee
import xarray as xr
import rioxarray  # noqa: F401
from dotenv import load_dotenv
from huggingface_hub import HfApi
from tqdm import tqdm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'google-earth'))

from logger import get_logger  # type: ignore[reportMissingImports]
from config import (  # type: ignore[reportMissingImports]
    PROJECT_ID, CALI, FUENTES, DISPONIBILIDAD, ESCALA_OVERRIDE,
)
from _apilar import apilar_bandas  # type: ignore[reportMissingImports]

BYTES_DTYPE = {
    'int8': 1, 'uint8': 1, 'int16': 2, 'uint16': 2,
    'int32': 4, 'uint32': 4, 'float': 4, 'float32': 4,
    'int64': 8, 'uint64': 8, 'double': 8, 'float64': 8,
}

MAX_BATCH_BYTES = 8 * 1024**3
MIN_DISCO_LIBRE_GB = 5
COMMITS_POR_HORA = 110
SEGUNDOS_ENTRE_COMMITS = 3600 / COMMITS_POR_HORA

log = get_logger('subida_masiva')
load_dotenv()
HF_TOKEN = os.environ['HF_TOKEN']
DATASET = os.environ['DATASET'].lstrip('/')

WORK_ROOT = os.path.join(ROOT, 'hugging-face', 'descargas')
STAGING = os.path.join(WORK_ROOT, '_stage')
CACHE_ROOT = os.path.join(ROOT, 'hugging-face', 'cache')
os.makedirs(STAGING, exist_ok=True)
os.makedirs(CACHE_ROOT, exist_ok=True)

ee.Initialize(project=PROJECT_ID)
region = ee.Geometry.Rectangle(CALI)
xmin, ymin, xmax, ymax = CALI
lat_media = (ymin + ymax) / 2
ancho_m = (xmax - xmin) * 111_320 * math.cos(math.radians(lat_media))
alto_m = (ymax - ymin) * 110_540


def cache_path(fuente):
    return os.path.join(CACHE_ROOT, fuente.replace('/', '_').lower() + '.json')


def cargar_cache(fuente):
    p = cache_path(fuente)
    if os.path.exists(p):
        return set(json.load(open(p)))
    return set()


def guardar_cache(fuente, ids):
    json.dump(sorted(ids), open(cache_path(fuente), 'w'))


def disco_libre_gb(path):
    return shutil.disk_usage(path).free / 1024**3


def info_fuente(fuente):
    primera = (ee.ImageCollection(fuente)
               .filterBounds(region)
               .filterDate(*DISPONIBILIDAD[fuente])
               .first())
    info = primera.getInfo()
    bandas = info.get('bands', [])
    nominal = primera.select(0).projection().nominalScale().getInfo()
    escala_m = ESCALA_OVERRIDE.get(fuente, nominal)
    bytes_px = sum(
        BYTES_DTYPE.get(b.get('data_type', {}).get('precision', ''), 4)
        for b in bandas
    )
    pixeles = math.ceil(ancho_m / escala_m) * math.ceil(alto_m / escala_m)
    return escala_m, pixeles * bytes_px


def listar_ids(fuente):
    ini, fin = DISPONIBILIDAD[fuente]
    return (ee.ImageCollection(fuente)
            .filterBounds(region)
            .filterDate(ini, fin)
            .aggregate_array('system:index')
            .getInfo()) or []


def hacer_batches(ids, peso_img):
    if peso_img >= MAX_BATCH_BYTES:
        return [[i] for i in ids]
    n = max(1, MAX_BATCH_BYTES // peso_img)
    return [ids[i:i+n] for i in range(0, len(ids), n)]


def descargar_imagen_por_bandas(fuente, img_id, escala_m, raw_dir):
    imagen = ee.Image(f"{fuente}/{img_id}").clip(region)
    bandas = imagen.bandNames().getInfo() or []
    for banda in bandas:
        destino = os.path.join(raw_dir, f'{img_id}__{banda}.tif')
        if os.path.exists(destino):
            continue
        url = imagen.select(banda).getDownloadURL({
            'region': region,
            'scale': escala_m,
            'crs': 'EPSG:4326',
            'format': 'GEO_TIFF',
        })
        r = requests.get(url, timeout=600)
        r.raise_for_status()
        with open(destino, 'wb') as f:
            f.write(r.content)
    return bandas


def construir_zarr_batch(raw_dir, zarr_path):
    por_imagen = {}
    for fname in sorted(os.listdir(raw_dir)):
        if not fname.endswith('.tif') or '__' not in fname:
            continue
        img_id, resto = fname.split('__', 1)
        banda = resto[:-4]
        por_imagen.setdefault(img_id, {})[banda] = os.path.join(raw_dir, fname)

    datasets = []
    for img_id in sorted(por_imagen):
        arrs = {}
        for banda, path in por_imagen[img_id].items():
            da = rioxarray.open_rasterio(path)
            if isinstance(da, list):
                da = da[0]
            arrs[banda] = da.squeeze('band', drop=True)
        ds = xr.Dataset(arrs).expand_dims(time=[img_id])
        datasets.append(ds)
    xr.concat(datasets, dim='time').to_zarr(zarr_path, mode='w', consolidated=True, zarr_format=2)


def procesar_fuente(fuente, api, max_batches=None):
    nombre = fuente.replace('/', '_').lower()
    log.info(f"==== {fuente} ====")
    escala_m, peso_img = info_fuente(fuente)
    log.info(f"  Escala: {escala_m:.1f} m/px | peso/img: {peso_img/1024**2:.2f} MB")

    todos = listar_ids(fuente)
    hechos = cargar_cache(fuente)
    pendientes = [i for i in todos if i not in hechos]
    log.info(f"  Imagenes total: {len(todos):,} | hechos: {len(hechos):,} | "
             f"pendientes: {len(pendientes):,}")

    batches = hacer_batches(pendientes, peso_img)
    log.info(f"  Batches a procesar: {len(batches)}")

    for n_batch, ids in enumerate(batches, 1):
        if max_batches and n_batch > max_batches:
            log.info(f"  Limite de batches alcanzado ({max_batches})")
            break

        if disco_libre_gb(WORK_ROOT) < MIN_DISCO_LIBRE_GB:
            log.warning(f"  Disco libre < {MIN_DISCO_LIBRE_GB} GB, abortando")
            return

        batch_id = f"{n_batch:05d}_{ids[0]}"
        batch_dir = os.path.join(STAGING, nombre, batch_id)
        raw_dir = os.path.join(batch_dir, 'raw')
        zarr_path = os.path.join(batch_dir, 'zarr', f'{batch_id}.zarr')
        os.makedirs(raw_dir, exist_ok=True)
        os.makedirs(os.path.dirname(zarr_path), exist_ok=True)

        log.info(f"  [{n_batch}/{len(batches)}] batch {batch_id} "
                 f"({len(ids)} imgs, est {len(ids)*peso_img/1024**2:.1f} MB)")

        bandas_por_img = {}
        for img_id in tqdm(ids, desc='    descargando', unit='img', leave=False):
            try:
                bandas_por_img[img_id] = descargar_imagen_por_bandas(
                    fuente, img_id, escala_m, raw_dir
                )
            except Exception as e:
                log.warning(f"    skip {img_id}: {e}")

        construir_zarr_batch(raw_dir, zarr_path)

        for img_id, bandas in bandas_por_img.items():
            apilar_bandas(raw_dir, img_id, bandas,
                          os.path.join(raw_dir, f'{img_id}.tif'))

        t0 = time.time()
        api.upload_large_folder(
            folder_path=STAGING,
            repo_id=DATASET,
            repo_type='dataset',
            num_workers=4,
            print_report=False,
        )
        log.info(f"    upload {time.time()-t0:.1f}s -> {nombre}/{batch_id}")

        hechos.update(bandas_por_img.keys())
        guardar_cache(fuente, hechos)

        shutil.rmtree(batch_dir, ignore_errors=True)
        time.sleep(SEGUNDOS_ENTRE_COMMITS)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--fuente', type=int, default=None,
                   help='indice en FUENTES (omitir = todas)')
    p.add_argument('--max-batches', type=int, default=None,
                   help='limite de batches por fuente para test')
    args = p.parse_args()

    api = HfApi(token=HF_TOKEN)
    api.create_repo(repo_id=DATASET, repo_type='dataset', exist_ok=True)

    fuentes = [FUENTES[args.fuente]] if args.fuente is not None else FUENTES
    for fuente in fuentes:
        procesar_fuente(fuente, api, max_batches=args.max_batches)


if __name__ == '__main__':
    try:
        main()
    finally:
        logging.shutdown()
