import os
import sys
import argparse
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
from google.cloud import storage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'google-earth'))

load_dotenv(os.path.join(ROOT, '.env'))

from config import PROJECT_ID
from logger import get_logger

GCS_BUCKET = 'fuentes-proyecto-3'
HF_BUCKET = 'yeigen/fuentes-proyecto-3'
DOWNLOAD_WORKERS = 8

DATASETS = {
    'era5':  ('ecmwf_era5_hourly',              'ERA5'),
    'no2':   ('copernicus_s5p_offl_l3_no2',      'S5P_NO2'),
    'so2':   ('copernicus_s5p_offl_l3_so2',      'S5P_SO2'),
    'o3':    ('copernicus_s5p_offl_l3_o3',        'S5P_O3'),
    'modis': ('modis_061_mcd19a2_granules',      'MODIS'),
    's2':    ('copernicus_s2_sr_harmonized',      'S2'),
}

GCS = storage.Client(project=PROJECT_ID)
bucket = GCS.bucket(GCS_BUCKET)


def descargar_zarr(prefix, name):
    staging = os.path.join(ROOT, 'hugging-face', 'staging', prefix)
    blobs = list(bucket.list_blobs(prefix=f'{prefix}/panel.zarr/'))
    if not blobs:
        log.error(f'{name}: no se encontraron archivos zarr en GCS')
        return 0

    os.makedirs(staging, exist_ok=True)

    def descargar(b):
        dest = os.path.join(staging, os.path.relpath(b.name, prefix))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        if os.path.exists(dest):
            return b.name, '(cache)'
        b.download_to_filename(dest)
        return b.name, f'{b.size / 1024:.1f}KB'

    with ThreadPoolExecutor(max_workers=DOWNLOAD_WORKERS) as ex:
        futuros = [ex.submit(descargar, b) for b in blobs]
        with tqdm(total=len(blobs), desc=f'  {name}', unit='file') as bar:
            for f in as_completed(futuros):
                f.result()
                bar.update(1)

    log.info(f'{name}: {len(blobs)} archivos zarr descargados')
    return len(blobs)


def subir_bucket(prefix=None):
    staging = os.path.join(ROOT, 'hugging-face', 'staging')
    src = os.path.join(staging, prefix) if prefix else staging

    cmd = ['hf', 'buckets', 'sync', src, f'hf://buckets/{HF_BUCKET}']
    log.info(f'Ejecutando: {" ".join(cmd)}')
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log.error(f'Error en sync: {result.stderr}')
        return False
    log.info(result.stdout)
    return True


def main():
    p = argparse.ArgumentParser(description='Subir datasets zarr a HuggingFace Bucket')
    p.add_argument('--dataset', choices=list(DATASETS.keys()) + ['all'], default='all',
                   help='Dataset a subir (default: all)')
    p.add_argument('--skip-download', action='store_true', help='No descargar de GCS, usar cache local')
    p.add_argument('--only-sync', action='store_true', help='Solo sync al bucket, no descargar')
    args = p.parse_args()

    global log
    log = get_logger('subir_hf')

    datasets = list(DATASETS.items()) if args.dataset == 'all' else [(args.dataset, DATASETS[args.dataset])]

    for key, (prefix, name) in datasets:
        log.info(f'=== Procesando {name} ({prefix}) ===')

        if not args.skip_download and not args.only_sync:
            descargar_zarr(prefix, name)

    prefix_filter = None if args.dataset == 'all' else DATASETS[args.dataset][0]
    subir_bucket(prefix_filter)

    log.info('Completado')


if __name__ == '__main__':
    main()