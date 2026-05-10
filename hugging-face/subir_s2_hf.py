"""
Subir panel.zarr de Sentinel-2 desde GCS al bucket HuggingFace.

Diseñado para ejecutarse en el droplet, donde la red GCS↔HF es ~1 Gbps.
Estrategia: descargar GCS → staging local → `hf buckets sync` → cleanup.

Uso:
    .venv/bin/python hugging-face/subir_s2_hf.py [--esperar-pid PID]
    .venv/bin/python hugging-face/subir_s2_hf.py --solo-verificar
"""
import os
import sys
import time
import argparse
import subprocess
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
from google.cloud import storage
from tqdm import tqdm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'google-earth'))

load_dotenv(os.path.join(ROOT, '.env'))

from config import PROJECT_ID
from logger import get_logger

log = get_logger('subir_s2_hf')

GCS_BUCKET = 'fuentes-proyecto-3'
HF_BUCKET = 'yeigen/fuentes-proyecto-3'
PREFIJO = 'copernicus_s2_sr_harmonized'
ZARR_PREFIX = f'{PREFIJO}/panel.zarr'
STAGING = os.path.join(ROOT, 'hugging-face', 'staging', PREFIJO)

DOWNLOAD_WORKERS = 16


def proceso_vivo(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError):
        return False


def esperar_proceso(pid, intervalo=120):
    log.info(f'Esperando que el PID {pid} termine antes de subir...')
    while proceso_vivo(pid):
        time.sleep(intervalo)
    log.info(f'PID {pid} ya no esta corriendo. Continuando.')


def listar_blobs_zarr(bucket):
    blobs = list(bucket.list_blobs(prefix=f'{ZARR_PREFIX}/'))
    consolidado = any(b.name.endswith('/.zmetadata') for b in blobs)
    peso = sum(b.size for b in blobs) / 1024**3
    return blobs, consolidado, peso


def verificar_gcs(bucket):
    blobs, consolidado, peso = listar_blobs_zarr(bucket)
    log.info(f'GCS panel.zarr: {len(blobs):,} blobs | {peso:.2f} GB | consolidado: {consolidado}')
    if peso < 40:
        log.error(f'Peso ({peso:.2f} GB) por debajo del umbral de tolerancia (40 GB). Abortando.')
        return False
    if not consolidado:
        log.warning('.zmetadata no encontrado — el Zarr no esta consolidado. '
                    'Sigue siendo subible pero los clientes deberan abrir con consolidated=False.')
    return True


def descargar_panel(bucket):
    blobs, _, _ = listar_blobs_zarr(bucket)
    log.info(f'Descargando {len(blobs):,} archivos a {STAGING}')
    os.makedirs(STAGING, exist_ok=True)

    def descargar_uno(blob):
        relativo = os.path.relpath(blob.name, PREFIJO)
        destino = os.path.join(STAGING, relativo)
        if os.path.exists(destino) and os.path.getsize(destino) == blob.size:
            return blob.name, True, '(cache)'
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        blob.download_to_filename(destino)
        return blob.name, True, f'{blob.size/1024**2:.1f}MB'

    fallas = []
    with ThreadPoolExecutor(max_workers=DOWNLOAD_WORKERS) as ex:
        futuros = [ex.submit(descargar_uno, b) for b in blobs]
        with tqdm(total=len(blobs), desc='GCS→local', unit='file') as bar:
            for f in as_completed(futuros):
                try:
                    name, ok, info = f.result()
                    if not ok:
                        fallas.append(name)
                except Exception as e:
                    fallas.append(str(e))
                bar.update(1)

    if fallas:
        log.error(f'{len(fallas)} archivos fallaron al descargar')
        return False

    peso_local = sum(
        os.path.getsize(os.path.join(r, f))
        for r, _, fs in os.walk(STAGING)
        for f in fs
    ) / 1024**3
    log.info(f'Descarga completa: {peso_local:.2f} GB en disco')
    return True


def sync_a_hf():
    cmd = ['hf', 'buckets', 'sync', STAGING, f'hf://buckets/{HF_BUCKET}/{PREFIJO}']
    log.info(f'Ejecutando: {" ".join(cmd)}')
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log.error(f'hf buckets sync fallo: {result.stderr}')
        return False
    log.info(result.stdout)
    return True


def verificar_hf():
    cmd = ['hf', 'buckets', 'ls', f'hf://buckets/{HF_BUCKET}/{PREFIJO}/panel.zarr/']
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log.warning(f'No se pudo listar HF: {result.stderr}')
        return None
    n_hf = sum(1 for line in result.stdout.splitlines() if line.strip())
    log.info(f'HF panel.zarr: {n_hf} archivos visibles')
    return n_hf


def limpiar_staging(confirmar):
    if not confirmar:
        log.info(f'Manteniendo staging en {STAGING} (usar --limpiar para borrar)')
        return
    log.info(f'Borrando staging {STAGING}')
    shutil.rmtree(STAGING, ignore_errors=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--esperar-pid', type=int, default=None,
                   help='PID del proceso S2→Zarr a esperar antes de empezar')
    p.add_argument('--solo-verificar', action='store_true',
                   help='Solo verificar el estado GCS, sin descargar ni subir')
    p.add_argument('--skip-download', action='store_true',
                   help='No descargar de GCS (asumir staging ya tiene los datos)')
    p.add_argument('--limpiar', action='store_true',
                   help='Borrar staging al terminar')
    args = p.parse_args()

    cliente = storage.Client(project=PROJECT_ID)
    bucket = cliente.bucket(GCS_BUCKET)

    if args.esperar_pid:
        esperar_proceso(args.esperar_pid)

    if not verificar_gcs(bucket):
        sys.exit(1)

    if args.solo_verificar:
        log.info('Modo solo-verificar: terminando sin tocar HF.')
        return

    if not args.skip_download:
        if not descargar_panel(bucket):
            sys.exit(2)

    if not sync_a_hf():
        sys.exit(3)

    verificar_hf()
    limpiar_staging(args.limpiar)
    log.info('Subida S2 → HF completada')


if __name__ == '__main__':
    main()
