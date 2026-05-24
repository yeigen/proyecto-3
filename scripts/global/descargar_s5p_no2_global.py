import os, sys, urllib.request
import ee

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'google-earth'))
sys.path.insert(0, os.path.join(HERE, '..', '..'))
from config import PROJECT_ID
from logger import get_logger

log = get_logger('s5p_no2_global')
ee.Initialize(project=PROJECT_ID)

OUT = os.path.join(HERE, '..', '..', 'docs', 'situacion-1', 'evidencias',
                   'fuentes', 'google-earth', 'globales')
os.makedirs(OUT, exist_ok=True)

col = (ee.ImageCollection('COPERNICUS/S5P/OFFL/L3_NO2')
       .filterDate('2024-01-01', '2024-06-01'))

VIZ = {'bands': ['tropospheric_NO2_column_number_density'],
       'min': 0, 'max': 0.0002,
       'palette': ['black', 'blue', 'purple', 'cyan', 'green', 'yellow', 'red']}

try:
    img = col.mean().select('tropospheric_NO2_column_number_density').unmask(0)
    url = img.getThumbURL({**VIZ, 'dimensions': 1024, 'format': 'png'})
    fname = 's5p_no2.png'
    urllib.request.urlretrieve(url, os.path.join(OUT, fname))
    log.info(f'OK  {fname}')
except Exception as e:
    log.warning(f'ERR NO2 global: {e}')
