# Panel final

## Qué contiene

Resumen del entregable principal de Situación 1: un panel multi-fuente publicado y trazable para el resto del proyecto.

## Resultado

- Panel longitudinal 2021-2025 sobre Cali, Yumbo y Acopi.
- BBox operativo: `[-76.65, 3.30, -76.30, 3.65]`.
- 6 fuentes satelitales/atmosféricas principales más DAGMA/CVC.
- Datos en GeoTIFF raw y Zarr analítico.
- Publicación en GCS, Hugging Face y Kaggle.
- Manifest con tamaños, archivos, hashes y metadatos.

## Tamaño y publicación

- Kaggle Dataset: 89.73 GB.
- Kaggle UI: 8,848 archivos.
- Manifest técnico: 8,847 archivos de datos.

La diferencia se debe a `dataset-metadata.json`, que Kaggle cuenta en su interfaz.

## Evidencias relacionadas

- [Dataset Kaggle](../evidencias/panel/sit1_panel_kaggle_dataset.png)
- [Bucket GCS](../evidencias/panel/sit1_panel_bucket_gcs.png)
- [Bucket Hugging Face](../evidencias/panel/sit1_panel_bucket_hugging_face.png)
- [Comparación de BBox](../evidencias/panel/sit1_panel_bbox_pdf_vs_proyecto.png)

## Referencias

- [Panel Zarr](../capas/panel-zarr.md)
- [Flujo de datos](../metodologia/flujo-datos.md)
- [Kaggle Dataset geovision-fuentes](https://www.kaggle.com/datasets/juanjoseorozcolopez/geovision-fuentes)
- [Manifest técnico](../../../manifest/manifest_output/manifest.json)
