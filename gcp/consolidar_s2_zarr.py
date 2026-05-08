"""
Consolida los GeoTIFFs S2 individuales en un Zarr 4D (time, band, y, x).

Soporta dos formatos en el bucket:
- Individual: {safe}__{banda}.tif (13 archivos por imagen)
- Cloud Optimized: {safe}__spectral.tif (12 bandas) + {safe}__scl.tif

Streaming por bloques de N imagenes para no saturar RAM/disco.

Uso:
  uv run python gcp/consolidar_s2_zarr.py --max-imagenes 20  # test con pocas
  uv run python gcp/consolidar_s2_zarr.py                    # todas
  uv run python gcp/consolidar_s2_zarr.py --reset            # borra Zarr previo
"""
import os
import sys
import time
import argparse
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

warnings.filterwarnings("ignore", category=UserWarning)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "google-earth"))

import ee
import numpy as np
import xarray as xr
import rasterio
import gcsfs
import zarr
from google.cloud import storage

from config import PROJECT_ID, CALI, BANDAS_UTILES, ESCALA_OVERRIDE, DISPONIBILIDAD
from logger import get_logger

log = get_logger("consolidar_s2_zarr")
ee.Initialize(project=PROJECT_ID)

BUCKET = "fuentes-proyecto-3"
ZARR_NAME = "panel.zarr"
BATCH_TIME = 5
WORKERS_DOWN = 4

fuente_id = "COPERNICUS/S2_SR_HARMONIZED"
ini, fin = DISPONIBILIDAD[fuente_id]
escala_m = ESCALA_OVERRIDE[fuente_id]
prefijo = fuente_id.replace("/", "_").lower()
region = ee.Geometry.Rectangle(CALI)
bandas_all = BANDAS_UTILES[fuente_id]
bandas_individuales = [b for b in bandas_all if b != "SCL"]

storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET)
fs = gcsfs.GCSFileSystem()


def parse_fecha(img_id):
    return datetime.strptime(img_id[:15], "%Y%m%dT%H%M%S")


def cargar_individual(safe, existentes):
    arrays = {}
    for b in bandas_all:
        path = f"{prefijo}/raw/{safe}__{b}.tif"
        if path not in existentes:
            return None
        data = bucket.blob(path).download_as_bytes()
        with rasterio.MemoryFile(data) as mf:
            with mf.open() as ds:
                arrays[b] = ds.read(1).astype("uint16")
    return np.stack([arrays[b] for b in bandas_all], axis=0)


def cargar_cloudoptimized(safe, existentes):
    sp_path = f"{prefijo}/raw/{safe}__spectral.tif"
    scl_path = f"{prefijo}/raw/{safe}__scl.tif"
    if sp_path not in existentes or scl_path not in existentes:
        return None
    sp_data = bucket.blob(sp_path).download_as_bytes()
    with rasterio.MemoryFile(sp_data) as mf:
        with mf.open() as ds:
            sp = ds.read().astype("uint16")  # (12, H, W)
    scl_data = bucket.blob(scl_path).download_as_bytes()
    with rasterio.MemoryFile(scl_data) as mf:
        with mf.open() as ds:
            scl = ds.read(1).astype("uint16")[None, ...]  # (1, H, W)
    return np.concatenate([sp, scl], axis=0)


def cargar_imagen(img_id, existentes):
    safe = img_id.replace("/", "_")
    arr = cargar_individual(safe, existentes)
    if arr is not None:
        return img_id, arr, "individual"
    arr = cargar_cloudoptimized(safe, existentes)
    if arr is not None:
        return img_id, arr, "cloudopt"
    return img_id, None, "missing"


def construir_bloque(ids, existentes):
    resultados = []
    with ThreadPoolExecutor(max_workers=WORKERS_DOWN) as ex:
        futs = {ex.submit(cargar_imagen, iid, existentes): iid for iid in ids}
        for f in as_completed(futs):
            try:
                resultados.append(f.result())
            except Exception as e:
                iid = futs[f]
                log.warning(f"  fallo {iid}: {type(e).__name__}: {str(e)[:100]}")

    validas = [(iid, arr) for iid, arr, _ in resultados if arr is not None]
    log.info(f"  Validas: {len(validas)}/{len(ids)}")
    if not validas:
        return None

    validas.sort(key=lambda x: parse_fecha(x[0]))
    img_ids = [v[0] for v in validas]
    arrays = [v[1] for v in validas]
    fechas = [parse_fecha(iid) for iid in img_ids]

    stack = np.stack(arrays, axis=0)
    return xr.Dataset(
        {"reflectance": (("time", "band", "y", "x"), stack)},
        coords={
            "time": fechas,
            "band": bandas_all,
            "image_id": ("time", img_ids),
        },
        attrs={
            "bbox": str(CALI),
            "fuente": fuente_id,
            "escala_m": escala_m,
            "crs": "EPSG:4326",
        },
    )


def borrar_zarr_previo():
    blobs = list(storage_client.list_blobs(BUCKET, prefix=f"{prefijo}/{ZARR_NAME}/"))
    log.info(f"Borrando Zarr previo: {len(blobs)} blobs")
    if not blobs:
        return
    with ThreadPoolExecutor(max_workers=32) as ex:
        list(ex.map(lambda b: b.delete(), blobs))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--max-imagenes", type=int, default=None)
    p.add_argument("--reset", action="store_true",
                   help="Borrar Zarr previo antes de empezar")
    p.add_argument("--batch", type=int, default=BATCH_TIME,
                   help="Imagenes por bloque temporal")
    p.add_argument("--solo-existentes", action="store_true",
                   help="Solo consolidar IDs que ya tienen archivos en el bucket")
    args = p.parse_args()

    log.info("Listando blobs S2 en bucket...")
    existentes = set(b.name for b in storage_client.list_blobs(
        BUCKET, prefix=f"{prefijo}/raw/"))
    log.info(f"Blobs S2 existentes: {len(existentes)}")

    log.info("Listando IDs S2 en GEE...")
    ids = (ee.ImageCollection(fuente_id)
           .filterBounds(region)
           .filterDate(ini, fin)
           .aggregate_array("system:index").getInfo())

    if args.solo_existentes:
        ids_filtrados = []
        for iid in ids:
            safe = iid.replace("/", "_")
            tiene_individual = all(
                f"{prefijo}/raw/{safe}__{b}.tif" in existentes for b in bandas_all
            )
            tiene_cloudopt = (
                f"{prefijo}/raw/{safe}__spectral.tif" in existentes
                and f"{prefijo}/raw/{safe}__scl.tif" in existentes
            )
            if tiene_individual or tiene_cloudopt:
                ids_filtrados.append(iid)
        log.info(f"Filtrado: {len(ids_filtrados)} de {len(ids)} tienen archivos en bucket")
        ids = ids_filtrados

    if args.max_imagenes:
        ids = ids[:args.max_imagenes]
    log.info(f"Total IDs a consolidar: {len(ids)}")

    if args.reset:
        borrar_zarr_previo()

    store_path = f"{BUCKET}/{prefijo}/{ZARR_NAME}"
    store = fs.get_mapper(store_path)

    bloques = [ids[i:i + args.batch] for i in range(0, len(ids), args.batch)]
    log.info(f"Bloques: {len(bloques)} x ~{args.batch} imagenes")

    H, W = 3897, 3897
    encoding = {
        "reflectance": {
            "chunks": (args.batch, len(bandas_all), 1024, 1024),
        }
    }

    primera_escritura = True
    total_imgs = 0
    t_total = time.time()
    for i, bloque in enumerate(bloques, 1):
        t0 = time.time()
        log.info(f"[{i}/{len(bloques)}] Cargando {len(bloque)} imagenes...")
        ds = construir_bloque(bloque, existentes)
        if ds is None:
            log.warning(f"  Bloque {i} vacio, skip")
            continue

        if primera_escritura:
            ds.to_zarr(store, mode="w", consolidated=True, encoding=encoding)
            primera_escritura = False
        else:
            ds.to_zarr(store, mode="a", append_dim="time")

        total_imgs += ds.sizes["time"]
        dt = time.time() - t0
        log.info(f"  Bloque {i}: +{ds.sizes['time']} imgs ({total_imgs} total) en {dt:.0f}s")

    log.info("Reconsolidando metadata...")
    zarr.consolidate_metadata(store)

    total_bytes = sum(b.size for b in storage_client.list_blobs(
        BUCKET, prefix=f"{prefijo}/{ZARR_NAME}/"))
    log.info(f"Zarr final: {total_bytes/1024**3:.2f} GB | "
             f"{total_imgs} imagenes en {(time.time()-t_total)/60:.0f} min")
    log.info(f"Path: gs://{BUCKET}/{prefijo}/{ZARR_NAME}/")


if __name__ == "__main__":
    main()
