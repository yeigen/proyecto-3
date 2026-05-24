import os, sys, urllib.request
import ee

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'google-earth'))
sys.path.insert(0, os.path.join(HERE, '..', '..'))
from config import PROJECT_ID
from logger import get_logger

log = get_logger('era5_global')
ee.Initialize(project=PROJECT_ID)

OUT = os.path.join(HERE, '..', '..', 'docs', 'situacion-1', 'evidencias',
                   'fuentes', 'google-earth', 'globales')
os.makedirs(OUT, exist_ok=True)

VARS = [
    ('temperature_2m',          250, 320, ['blue','cyan','green','yellow','red']),
    ('boundary_layer_height',   0,   2000,['black','purple','blue','cyan','green','yellow','red']),
    ('u_component_of_wind_10m', -15, 15,  ['red','white','blue']),
    ('total_precipitation',     0,   0.05,['white','yellow','green','blue','red']),
]

for banda, vmin, vmax, pal in VARS:
    try:
        img = (ee.ImageCollection('ECMWF/ERA5/HOURLY')
               .filterDate('2024-07-15T12:00', '2024-07-15T13:00')
               .first()
               .select(banda)
               .unmask(vmin))
        viz = {'bands': [banda], 'min': vmin, 'max': vmax, 'palette': pal}
        url = img.getThumbURL({**viz, 'dimensions': 1024, 'format': 'png'})
        fname = f'era5_{banda}.png'
        urllib.request.urlretrieve(url, os.path.join(OUT, fname))
        log.info(f'OK  {fname}')
    except Exception as e:
        log.warning(f'ERR {banda}: {e}')
