# Situación 2

Entrenamiento y auditoría del flujo CLIP + SAE usando tiles Sentinel-2 generados desde el panel de Situación 1.

## Índice por capas

- [Fuentes](fuentes/)
- [Capas](capas/)
- [Metodología](metodologia/)
- [Evidencias](evidencias/README.md)
- [Resultados](resultados/)
- [Referencias](referencias.md)

## Resumen

La Situación 2 toma el panel satelital validado en Situación 1 y genera 5,000 tiles balanceados para entrenar un modelo CLIP fine-tuneado con LoRA. Después se analizan embeddings con SAE, AFE y AFC.

## Documentos principales

### Fuentes y capas

- [Fuentes usadas](fuentes/fuentes-sit2.md)
- [Tiles Sentinel-2](capas/tiles-sentinel-2.md)
- [Pseudo-labels S5P](capas/pseudo-labels-s5p.md)
- [Contexto ERA5 y MODIS](capas/contexto-era5-modis.md)

### Metodología

- [Muestreo estratificado](metodologia/muestreo.md)
- [Arquitectura CLIP + SAE](metodologia/arquitectura-clip-sae.md)
- [Entrenamiento](metodologia/entrenamiento.md)
- [Auditoría de sesgos](metodologia/auditoria-sesgos.md)

### Resultados

- [Resultados de muestreo](resultados/resultados-muestreo.md)
- [Resultados CLIP](resultados/resultados-clip.md)
- [Resultados CLIP Sit 2.1 reparación](resultados/resultados-clip-sit2-1-reparacion.md)
- [Resultados CLIP Sit 2.17 pseudo-label retrieval](resultados/resultados-clip-sit2-17-pseudolabel.md)
- [Resultados SAE, AFE y AFC](resultados/resultados-sae-afe-afc.md)
- [Auditoría DAGMA/CVC](resultados/auditoria-dagma-cvc.md)

## Documentos originales

- [Muestreo Sit 2](MUESTREO_SIT2.md)
- [CLIP + SAE Sit 2](SIT2_CLIP_SAE.md)
- [Entrenamiento Sit 2](SIT2_ENTRENAMIENTO.md)
- [Auditoría de sesgos Sit 1 → Sit 2](AUDITORIA_SESGOS_SIT1_SIT2.md)
