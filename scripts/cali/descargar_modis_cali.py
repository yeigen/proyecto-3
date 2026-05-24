import os, sys, urllib.request
import ee

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'google-earth'))
sys.path.insert(0, os.path.join(HERE, '..', '..'))
from config import PROJECT_ID
from logger import get_logger

log = get_logger('modis_cali')
ee.Initialize(project=PROJECT_ID)

OUT = os.path.join(HERE, '..', '..', 'docs', 'situacion-1', 'evidencias',
                   'fuentes', 'google-earth', 'cali', 'modis_maiact')
os.makedirs(OUT, exist_ok=True)

cali = ee.Geometry.Rectangle([-76.65, 3.30, -76.30, 3.65])

FECHAS = ['2024-02-01', '2024-06-01', '2024-10-01', '2025-01-01']

VIZ = {'bands': ['Optical_Depth_047'],
       'min': 0, 'max': 1100,
       'palette': ['black', 'blue', 'purple', 'cyan', 'green', 'yellow', 'red']}

for fecha in FECHAS:
    try:
        img = (ee.ImageCollection('MODIS/061/MCD19A2_GRANULES')
               .filterBounds(cali)
               .filterDate(fecha, f'{fecha[:7]}-28')
               .first()
               .select('Optical_Depth_047')
               .unmask(0)
               .clip(cali))
        url = img.getThumbURL({**VIZ, 'dimensions': 512, 'region': cali, 'format': 'png'})
        fname = f'{fecha}.png'
        urllib.request.urlretrieve(url, os.path.join(OUT, fname))
        log.info(f'OK  {fname}')
    except Exception as e:
        log.warning(f'ERR {fecha}: {e}')
