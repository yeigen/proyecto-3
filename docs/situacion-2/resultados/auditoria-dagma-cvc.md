# Auditoría DAGMA/CVC

## Qué contiene

Cruce de tiles de Situación 2 con observaciones oficiales DAGMA/CVC por estación cercana y ventanas temporales.

## Resultado

| Contaminante | Cobertura mismo día | Cobertura ±3 días | Distancia mediana | Lectura |
|---|---:|---:|---:|---|
| NO2 | 8.2% | 9.5% | 16.58 km | Coherencia puntual en mismo día |
| SO2 | 10.8% | 11.9% | 5.65 km | No respalda la clase SO2 |
| O3 | 18.7% | 19.8% | 5.00 km | Coherencia puntual en mismo día |

## Interpretación

Esta auditoría no valida CLIP como predictor final. Sirve como puente hacia Situación 3 y acota el significado de las pseudo-etiquetas satelitales.

## Referencias

- [Auditoría de sesgos](../metodologia/auditoria-sesgos.md)
- [Auditoría original](../AUDITORIA_SESGOS_SIT1_SIT2.md)
- [Notebook auditoría puente](../../../notebooks/sit2/07_auditoria_puente_dagma_tiles.ipynb)
- [DAGMA/CVC en Situación 1](../../situacion-1/fuentes/dagma-cvc.md)
