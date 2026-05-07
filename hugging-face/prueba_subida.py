import os
import sys
import shutil
import logging
import warnings
import requests
import ee
import xarray as xr
import rioxarray
from dotenv import load_dotenv
from huggingface_hub import HfApi

warnings.filterwarnings('ignore', message='It seems you are trying to upload a large folder')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'google-earth'))

from logger import get_logger  # type: ignore[reportMissingImports]
from config import (  # type: ignore[reportMissingImports]
    PROJECT_ID, CALI, FUENTES, DISPONIBILIDAD, ESCALA_OVERRIDE, BANDAS_UTILES,
)
from _apilar import apilar_bandas  # type: ignore[reportMissingImports]

log = get_logger('prueba_subida')

load_dotenv()
HF_TOKEN = os.environ['HF_TOKEN']
DATASET = os.environ['DATASET'].lstrip('/')

WORK_DIR = os.path.join(ROOT, 'hugging-face', 'descargas', '_prueba')
shutil.rmtree(WORK_DIR, ignore_errors=True)
os.makedirs(WORK_DIR, exist_ok=True)

ee.Initialize(project=PROJECT_ID)
region = ee.Geometry.Rectangle(CALI)


def descargar_banda(imagen, banda, escala_m, destino):
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


def construir_zarr(raw_dir, zarr_path, img_id):
    arrs = {}
    for fname in sorted(os.listdir(raw_dir)):
        if not (fname.startswith(img_id + '__') and fname.endswith('.tif')):
            continue
        banda = fname[len(img_id) + 2:-4]
        da = rioxarray.open_rasterio(os.path.join(raw_dir, fname))
        if isinstance(da, list):
            da = da[0]
        arrs[banda] = da.squeeze('band', drop=True)
    xr.Dataset(arrs).to_zarr(zarr_path, mode='w', consolidated=True, zarr_format=2)


for fuente in FUENTES:
    nombre = fuente.replace('/', '_').lower()
    ini, fin = DISPONIBILIDAD[fuente]
    coleccion = (ee.ImageCollection(fuente)
                 .filterBounds(region)
                 .filterDate(ini, fin))
    primera = coleccion.first()
    escala_m = ESCALA_OVERRIDE.get(
        fuente, primera.select(0).projection().nominalScale().getInfo()
    )
    img_id = primera.get('system:index').getInfo()
    disponibles = primera.bandNames().getInfo() or []
    filtro = BANDAS_UTILES.get(fuente)
    bandas = [b for b in filtro if b in disponibles] if filtro else disponibles

    log.info(f">>> {fuente}  (escala {escala_m:.1f} m/px, {len(bandas)} bandas)")
    log.info(f"  Imagen {img_id}")

    fuente_dir = os.path.join(WORK_DIR, nombre)
    raw_dir = os.path.join(fuente_dir, 'raw')
    zarr_path = os.path.join(fuente_dir, 'zarr', f'{img_id}.zarr')
    tif_path = os.path.join(raw_dir, f'{img_id}.tif')
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(os.path.dirname(zarr_path), exist_ok=True)

    imagen = ee.Image(f"{fuente}/{img_id}").clip(region)
    for banda in bandas:
        destino = os.path.join(raw_dir, f'{img_id}__{banda}.tif')
        try:
            descargar_banda(imagen, banda, escala_m, destino)
        except Exception as e:
            log.warning(f"    skip banda {banda}: {e}")
    log.info(f"  Bandas descargadas: {len([f for f in os.listdir(raw_dir) if f.startswith(img_id)])}")

    construir_zarr(raw_dir, zarr_path, img_id)
    apilar_bandas(raw_dir, img_id, bandas, tif_path)
    log.info(f"  Tif multi-banda: {os.path.getsize(tif_path)/1024:.1f} KB")


peso_total = sum(
    os.path.getsize(os.path.join(d, f))
    for d, _, fs in os.walk(WORK_DIR) for f in fs
)
log.info(f"Total local: {peso_total/1024**2:.2f} MB")

api = HfApi(token=HF_TOKEN)
api.create_repo(repo_id=DATASET, repo_type='dataset', exist_ok=True)
log.info(f"Subiendo a {DATASET}/_prueba")
api.upload_folder(
    folder_path=WORK_DIR,
    path_in_repo='_prueba',
    repo_id=DATASET,
    repo_type='dataset',
    commit_message='prueba: 1 imagen por fuente (raw por-banda + zarr)',
)
log.info(f"OK https://huggingface.co/datasets/{DATASET}/tree/main/_prueba")
logging.shutdown()
