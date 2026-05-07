import os
import rasterio


def apilar_bandas(raw_dir, img_id, bandas, out_path):
    paths = []
    for b in bandas:
        p = os.path.join(raw_dir, f'{img_id}__{b}.tif')
        if os.path.exists(p):
            paths.append((b, p))
    if not paths:
        return None

    with rasterio.open(paths[0][1]) as src0:
        meta = src0.meta.copy()
    meta.update(count=len(paths), dtype='float32', compress='lzw')
    meta.pop('nodata', None)

    with rasterio.open(out_path, 'w', **meta) as dst:
        for i, (b, p) in enumerate(paths, 1):
            with rasterio.open(p) as src:
                dst.write(src.read(1).astype('float32'), i)
            dst.set_band_description(i, b)

    for _, p in paths:
        os.remove(p)
    return out_path
