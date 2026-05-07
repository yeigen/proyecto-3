import os
import sys
import requests
from tqdm import tqdm
import ee
from dotenv import load_dotenv
from huggingface_hub import HfApi

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'google-earth'))

from logger import get_logger  # type: ignore[reportMissingImports]
from config import PROJECT_ID, CALI, FUENTES  # type: ignore[reportMissingImports]

log = get_logger('subida_archivos')

load_dotenv()
HF_TOKEN = os.environ['HF_TOKEN']
DATASET = os.environ['DATASET'].lstrip('/')

FUENTE_IDX = 5  # MODIS/061/MCD19A2_GRANULES (la mas liviana)
INICIO = '2021-04-01'
FIN = '2026-04-01'
LIMITE = 20  # imagenes para test inicial; subir luego cuando todo este verificado
ESCALA_M = 1000  # metros/pixel para descarga (MODIS nativa ~1km)

fuente = FUENTES[FUENTE_IDX]
nombre = fuente.replace('/', '_').lower()
out_dir = os.path.join(ROOT, 'hugging-face', 'descargas', nombre)
os.makedirs(out_dir, exist_ok=True)

ee.Initialize(project=PROJECT_ID)
region = ee.Geometry.Rectangle(CALI)

col = (ee.ImageCollection(fuente)
       .filterBounds(region)
       .filterDate(INICIO, FIN)
       .limit(LIMITE))

ids = col.aggregate_array('system:index').getInfo()
log.info(f"Fuente: {fuente}")
log.info(f"Imagenes a descargar (recortadas a Cali): {len(ids)}")
log.info(f"Carpeta local: {out_dir}")

for img_id in tqdm(ids, desc='descargando', unit='img'):
    imagen = ee.Image(f"{fuente}/{img_id}").clip(region)
    url = imagen.getDownloadURL({
        'region': region,
        'scale': ESCALA_M,
        'crs': 'EPSG:4326',
        'format': 'GEO_TIFF',
    })
    destino = os.path.join(out_dir, f"{img_id}.tif")
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    with open(destino, 'wb') as f:
        f.write(r.content)

total_mb = sum(os.path.getsize(os.path.join(out_dir, f))
               for f in os.listdir(out_dir)) / 1024**2
log.info(f"Descarga completa. Peso local: {total_mb:.2f} MB")

log.info("Subiendo a HuggingFace...")
api = HfApi(token=HF_TOKEN)
api.upload_folder(
    folder_path=out_dir,
    path_in_repo=f'{nombre}',
    repo_id=DATASET,
    repo_type='dataset',
)
log.info(f"Subido a https://huggingface.co/datasets/{DATASET}")
