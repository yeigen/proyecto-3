import os, sys, urllib.request
import ee

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'google-earth'))
sys.path.insert(0, os.path.join(HERE, '..', '..'))
from config import PROJECT_ID
from logger import get_logger

log = get_logger('modis_global')
ee.Initialize(project=PROJECT_ID)

OUT = os.path.join(HERE, '..', '..', 'docs', 'situacion-1', 'evidencias',
                   'fuentes', 'google-earth', 'globales')
os.makedirs(OUT, exist_ok=True)

VARS = [
    ('Optical_Depth_047', 0, 500, ['black','blue','purple','cyan','green','yellow','red']),
    ('Optical_Depth_055', 0, 500, ['black','blue','purple','cyan','green','yellow','red']),
    ('Column_WV',         0, 3000,['black','blue','cyan','green','yellow','red']),
]

for banda, vmin, vmax, pal in VARS:
    try:
        col = (ee.ImageCollection('MODIS/061/MCD19A2_GRANULES')
               .filterDate('2024-07-01', '2024-07-31')
               .filterBounds(ee.Geometry.Rectangle([-85, -60, -30, 15])))

        img = col.median().select(banda).unmask(vmin)
        viz = {'bands': [banda], 'min': vmin, 'max': vmax, 'palette': pal}
        url = img.getThumbURL({**viz, 'dimensions': 1024, 'format': 'png'})
        fname = f'modis_{banda}.png'
        urllib.request.urlretrieve(url, os.path.join(OUT, fname))
        log.info(f'OK  {fname}')
    except Exception as e:
        log.warning(f'ERR {banda}: {e}')
