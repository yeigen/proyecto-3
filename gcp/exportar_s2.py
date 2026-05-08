"""
Exportar Sentinel-2 a GCS via getDownloadURL por banda individual.
Bypass del cuello de botella GEE (3 tasks simultaneas en free tier).

Cada imagen genera 13 archivos: 1 por banda (12 espectrales + SCL).
Cada banda cabe en el limite de 50MB de getDownloadURL (~15-30 MB).

Idempotencia: skip si los 13 archivos individuales ya existen,
O si los 2 archivos del formato anterior (__spectral.tif + __scl.tif) existen.
"""
import os
import sys
import io
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "google-earth"))

import ee
from config import (
    PROJECT_ID, CALI, BANDAS_UTILES, ESCALA_OVERRIDE, DISPONIBILIDAD,
)
from logger import get_logger
from google.cloud import storage

log = get_logger("exportar_s2")
ee.Initialize(project=PROJECT_ID)

BUCKET = "fuentes-proyecto-3"
MAX_WORKERS = 6
TIMEOUT_REQ = 600

fuente_id = "COPERNICUS/S2_SR_HARMONIZED"
ini, fin = DISPONIBILIDAD[fuente_id]
escala_m = ESCALA_OVERRIDE[fuente_id]
prefijo = fuente_id.replace("/", "_").lower()
region = ee.Geometry.Rectangle(CALI)
bandas_all = BANDAS_UTILES[fuente_id]

storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET)

log.info(f"BBox: {CALI}")
log.info(f"Escala: {escala_m}m | Bandas {len(bandas_all)}: {bandas_all}")

log.info("Listando blobs existentes en bucket...")
existentes = set()
for b in storage_client.list_blobs(BUCKET, prefix=f"{prefijo}/raw/"):
    existentes.add(b.name)
log.info(f"Blobs existentes: {len(existentes)}")


def existe_imagen(safe):
    base = f"{prefijo}/raw/{safe}"
    fmt_individual = all(f"{base}__{b}.tif" in existentes for b in bandas_all)
    if fmt_individual:
        return True
    return (f"{base}__spectral.tif" in existentes
            and f"{base}__scl.tif" in existentes)


def existe_banda(safe, banda):
    return f"{prefijo}/raw/{safe}__{banda}.tif" in existentes


def bajar_banda(img_id, safe, banda):
    blob_path = f"{prefijo}/raw/{safe}__{banda}.tif"
    blob = bucket.blob(blob_path)
    if blob.exists():
        return banda, True, 0, "(cache)"
    try:
        img = ee.Image(f"{fuente_id}/{img_id}").select(banda).clip(region)
        url = img.getDownloadURL({
            "region": region,
            "scale": escala_m,
            "crs": "EPSG:4326",
            "format": "GEO_TIFF",
        })
        r = requests.get(url, timeout=TIMEOUT_REQ)
        r.raise_for_status()
        blob.upload_from_file(io.BytesIO(r.content), content_type="image/tiff")
        return banda, True, len(r.content), "ok"
    except Exception as e:
        return banda, False, 0, str(e)[:80]


ids = (
    ee.ImageCollection(fuente_id)
    .filterBounds(region)
    .filterDate(ini, fin)
    .aggregate_array("system:index")
    .getInfo()
)
log.info(f"Total imagenes en coleccion: {len(ids)}")

pendientes = []
hechas = 0
for img_id in ids:
    safe = img_id.replace("/", "_")
    if existe_imagen(safe):
        hechas += 1
        continue
    pendientes.append((img_id, safe))
log.info(f"Hechas: {hechas} | Pendientes: {len(pendientes)}")


t_total = time.time()
for n, (img_id, safe) in enumerate(pendientes, 1):
    t0 = time.time()
    bandas_pendientes = [b for b in bandas_all if not existe_banda(safe, b)]
    if not bandas_pendientes:
        continue

    bytes_img = 0
    fallas = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = [ex.submit(bajar_banda, img_id, safe, b) for b in bandas_pendientes]
        for f in as_completed(futs):
            banda, ok, sz, info = f.result()
            if ok:
                bytes_img += sz
            else:
                fallas += 1
                log.warning(f"  {safe[:40]} {banda}: {info}")

    dt = time.time() - t0
    if n <= 5 or n % 10 == 0:
        elapsed_total = time.time() - t_total
        eta_min = (elapsed_total / n) * (len(pendientes) - n) / 60
        log.info(
            f"[{n}/{len(pendientes)}] {safe[:40]} "
            f"| {bytes_img/1024**2:.0f}MB en {dt:.0f}s "
            f"| {fallas} fallas | ETA {eta_min:.0f}min"
        )

log.info(f"COMPLETO: {len(pendientes)} imagenes en {(time.time()-t_total)/60:.0f} min")
