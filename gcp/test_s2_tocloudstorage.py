"""
Prueba toCloudStorage con 1 imagen S2 antes de migrar masivamente.
Estrategia: 2 tasks por imagen (B* uint16 + SCL byte), sin cast.
"""
import os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "google-earth"))

import ee
from config import PROJECT_ID, CALI, BANDAS_UTILES, ESCALA_OVERRIDE
from logger import get_logger

log = get_logger("test_s2_tcs")
ee.Initialize(project=PROJECT_ID)

BUCKET = "fuentes-proyecto-3"
fuente_id = "COPERNICUS/S2_SR_HARMONIZED"
escala_m = ESCALA_OVERRIDE[fuente_id]
prefijo = fuente_id.replace("/", "_").lower()
region = ee.Geometry.Rectangle(CALI)

bandas_all = BANDAS_UTILES[fuente_id]
bandas_uint16 = [b for b in bandas_all if b != "SCL"]
bandas_byte = ["SCL"]

img_id = "20210106T153621_20210106T154053_T18NUJ"
safe = img_id.replace("/", "_")
img = ee.Image(f"{fuente_id}/{img_id}").clip(region)

log.info(f"BBox: {CALI}")
log.info(f"Imagen: {img_id}")
log.info(f"Bandas uint16 ({len(bandas_uint16)}): {bandas_uint16}")
log.info(f"Bandas byte ({len(bandas_byte)}): {bandas_byte}")


def lanzar(suffix, sub):
    t = ee.batch.Export.image.toCloudStorage(
        image=sub,
        description=f"test_{safe}_{suffix}"[:100],
        bucket=BUCKET,
        fileNamePrefix=f"{prefijo}/raw/{safe}__{suffix}",
        region=region,
        scale=escala_m,
        crs="EPSG:4326",
        maxPixels=int(1e10),
        fileFormat="GEO_TIFF",
        formatOptions={"cloudOptimized": True},
    )
    t.start()
    return t


t0 = time.time()
task_a = lanzar("spectral", img.select(bandas_uint16))
task_b = lanzar("scl", img.select(bandas_byte))
log.info(f"Lanzadas tasks {task_a.id} (spectral) y {task_b.id} (scl)")

estado_a, estado_b = "?", "?"
TIMEOUT_S = 600
while time.time() - t0 < TIMEOUT_S:
    estado_a = task_a.status()["state"]
    estado_b = task_b.status()["state"]
    elapsed = int(time.time() - t0)
    log.info(f"  [{elapsed:3d}s] spectral={estado_a}  scl={estado_b}")
    if estado_a in ("COMPLETED", "FAILED", "CANCELLED") and \
       estado_b in ("COMPLETED", "FAILED", "CANCELLED"):
        break
    time.sleep(15)

log.info(f"Estado final: spectral={estado_a}  scl={estado_b}")
for t, name in [(task_a, "spectral"), (task_b, "scl")]:
    st = t.status()
    log.info(f"  {name}: {st.get('state')} | error: {st.get('error_message','-')}")
