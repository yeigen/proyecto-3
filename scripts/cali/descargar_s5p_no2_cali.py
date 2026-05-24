import os, sys, urllib.request
import ee

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'google-earth'))
sys.path.insert(0, os.path.join(HERE, '..', '..'))
from config import PROJECT_ID
from logger import get_logger

log = get_logger('s5p_no2_cali')
ee.Initialize(project=PROJECT_ID)

OUT = os.path.join(HERE, '..', '..', 'docs', 'situacion-1', 'evidencias',
                   'fuentes', 'google-earth', 'cali', 's5p_no2')
os.makedirs(OUT, exist_ok=True)

cali = ee.Geometry.Rectangle([-76.65, 3.30, -76.30, 3.65])

TRIMESTRES = [
    ('2024-01-01', '2024-03-31', 'q1_2024'),
    ('2024-04-01', '2024-06-30', 'q2_2024'),
    ('2024-07-01', '2024-09-30', 'q3_2024'),
    ('2024-10-01', '2024-12-31', 'q4_2024'),
]

VIZ = {'bands': ['tropospheric_NO2_column_number_density'],
       'min': 0, 'max': 0.00008,
       'palette': ['black', 'blue', 'purple', 'cyan', 'green', 'yellow', 'red']}

for ini, fin, etiq in TRIMESTRES:
    try:
        img = (ee.ImageCollection('COPERNICUS/S5P/OFFL/L3_NO2')
               .filterBounds(cali)
               .filterDate(ini, fin)
               .mean()
               .select('tropospheric_NO2_column_number_density')
               .unmask(0)
               .clip(cali))
        url = img.getThumbURL({**VIZ, 'dimensions': 512, 'region': cali, 'format': 'png'})
        fname = f'{etiq}.png'
        urllib.request.urlretrieve(url, os.path.join(OUT, fname))
        log.info(f'OK  {fname}')
    except Exception as e:
        log.warning(f'ERR {etiq}: {e}')
