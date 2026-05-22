# Auditoría de sesgos

## Qué contiene

Resumen de riesgos metodológicos entre el panel de Situación 1 y el entrenamiento de Situación 2.

## Riesgos declarados

1. Split CLIP v3 aleatorio global, no temporal ni espacial.
2. `ozono_anomalo` usa O3 de columna total, no O3 superficial.
3. Sentinel-2 fue llevado a grilla 10 m con remuestreo de bandas nativas de 20 m y 60 m.
4. MODIS tuvo versiones rotas en GCS, aunque el dataset final de tiles contiene rangos físicos.
5. DAGMA/CVC respalda débilmente las pseudo-etiquetas, especialmente SO2.

## Veredicto

No se encontró un fallo que invalide las métricas principales de CLIP v3. Las métricas deben leerse como separabilidad bajo distribución mezclada, no como generalización temporal estricta.

## Referencias

- [Auditoría original](../AUDITORIA_SESGOS_SIT1_SIT2.md)
- [Entrenamiento](entrenamiento.md)
- [Pseudo-labels S5P](../capas/pseudo-labels-s5p.md)
- [Auditoría DAGMA/CVC](../resultados/auditoria-dagma-cvc.md)
