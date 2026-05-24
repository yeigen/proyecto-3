import os, sys, urllib.request
import ee

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'google-earth'))
sys.path.insert(0, os.path.join(HERE, '..', '..'))
from config import PROJECT_ID
from logger import get_logger

log = get_logger('s2_cali')
ee.Initialize(project=PROJECT_ID)

OUT = os.path.join(HERE, '..', '..', 'docs', 'situacion-1', 'evidencias',
                   'fuentes', 'google-earth', 'cali', 'sentinel2')
os.makedirs(OUT, exist_ok=True)

cali = ee.Geometry.Rectangle([-76.65, 3.30, -76.30, 3.65])

# Fechas con baja nubosidad tipica en Cali (estacion seca)
FECHAS = ['2024-01-01', '2024-07-01', '2024-12-01']

def mascara_scl(img):
    """Mascara SCL: conserva solo pixeles 'limpios' (codigos 4,5,6,7)."""
    scl = img.select('SCL')
    mascara = scl.eq(4).Or(scl.eq(5)).Or(scl.eq(6)).Or(scl.eq(7))
    return img.updateMask(mascara).divide(10000)

VIZ = {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 0.3}

for fecha in FECHAS:
    try:
        raw = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
               .filterBounds(cali)
               .filterDate(fecha, f'{fecha[:7]}-31')
               .first())

        # RGB con mascara SCL (pixeles nube/sombra = negro)
        img = mascara_scl(raw).unmask(0).clip(cali)

        url = img.getThumbURL({**VIZ, 'dimensions': 512, 'region': cali, 'format': 'png'})
        fname = f'{fecha}_rgb_sclmask.png'
        urllib.request.urlretrieve(url, os.path.join(OUT, fname))
        log.info(f'OK  {fname}')
    except Exception as e:
        log.warning(f'ERR {fecha}: {e}')
