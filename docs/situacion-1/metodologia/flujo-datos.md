# Flujo de datos

## Qué contiene

Resume el flujo operativo usado para construir, convertir, publicar y consumir el panel de Situación 1.

## Flujo

```text
Google Earth Engine
        ↓
GeoTIFF raw en Google Cloud Storage
        ↓
Conversión a paneles Zarr
        ↓
Publicación en Kaggle Dataset y Hugging Face
        ↓
Consumo por notebooks de Situación 2 y Situación 3
```

## Uso en la situación 1

Este flujo evita depender de descargas manuales o archivos sueltos. GCS conserva los GeoTIFF raw y paneles upstream; Kaggle concentra el dataset que usa el equipo; Hugging Face respalda paneles pequeños.

## Evidencias relacionadas

- [Bucket GCS](../evidencias/panel/sit1_panel_bucket_gcs.png)
- [Bucket Hugging Face](../evidencias/panel/sit1_panel_bucket_hugging_face.png)
- [Dataset Kaggle](../evidencias/panel/sit1_panel_kaggle_dataset.png)

## Referencias

- [Kaggle Dataset geovision-fuentes](https://www.kaggle.com/datasets/juanjoseorozcolopez/geovision-fuentes)
- [Hugging Face bucket yeigen/fuentes-proyecto-3](https://huggingface.co/buckets/yeigen/fuentes-proyecto-3)
- [Google Cloud Storage bucket fuentes-proyecto-3](https://console.cloud.google.com/storage/browser/fuentes-proyecto-3)
- [Flujo del proyecto](../../FLUJO_PROYECTO.md)
- [Scripts de exportación GEE](../../../gcp/)
