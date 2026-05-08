"""
S2 export: bandas en grupos de 2 para no exceder 50MB de getDownloadURL.
13 bandas → 7 grupos → 7 requests/imagen.
"""
import os, sys, io, time, json, requests
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "google-earth"))

import ee
from config import PROJECT_ID, CALI, DISPONIBILIDAD, ESCALA_OVERRIDE, BANDAS_UTILES
from logger import get_logger
from google.cloud import storage
from tqdm import tqdm

log = get_logger("s2_final")
ee.Initialize(project=PROJECT_ID)

BUCKET = "fuentes-proyecto-3"
MAX_WORKERS = 6

region = ee.Geometry.Rectangle(CALI)
client = storage.Client(project=PROJECT_ID)
bucket = client.bucket(BUCKET)

fuente_id = "COPERNICUS/S2_SR_HARMONIZED"
ini, fin = DISPONIBILIDAD[fuente_id]
bandas = BANDAS_UTILES[fuente_id]
escala_m = ESCALA_OVERRIDE[fuente_id]
prefijo = fuente_id.replace("/", "_").lower()

ids = (ee.ImageCollection(fuente_id).filterBounds(region).filterDate(ini, fin)
       .aggregate_array("system:index").getInfo())
log.info(f"S2: {len(ids)} imagenes, {len(bandas)} bandas, {escala_m}m")

GRUPOS = [bandas[i:i+2] for i in range(0, len(bandas), 2)]
log.info(f"Grupos: {len(GRUPOS)} x ~2 bandas")


def bajar_grupo(img_id, gbandas, gi):
    safe = img_id.replace("/", "_")
    blob_path = f"{prefijo}/raw/{safe}__g{gi}.tif"
    blob = bucket.blob(blob_path)
    if blob.exists():
        return True, 0
    imagen = ee.Image(f"{fuente_id}/{img_id}").select(gbandas).clip(region)
    url = imagen.getDownloadURL(dict(region=region, scale=escala_m,
                                      crs="EPSG:4326", format="GEO_TIFF"))
    r = requests.get(url, timeout=300)
    r.raise_for_status()
    blob.upload_from_file(io.BytesIO(r.content), content_type="image/tiff")
    return True, len(r.content)


for img_idx, img_id in enumerate(ids, 1):
    total = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = [ex.submit(bajar_grupo, img_id, g, gi)
                for gi, g in enumerate(GRUPOS)]
        for f in as_completed(futs):
            ok, sz = f.result()
            if ok: total += sz
    if img_idx % 20 == 0:
        log.info(f"  [{img_idx}/{len(ids)}] {img_id[:40]}... {total/1024**2:.0f}MB")

log.info(f"COMPLETADO: {len(ids)} imagenes")
