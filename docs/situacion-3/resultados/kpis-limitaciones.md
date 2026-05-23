# KPIs y limitaciones

## Qué contiene

Resumen de KPIs, resultados y limitaciones principales de Situación 3.

## KPIs

| KPI | Meta | Resultado | Estado |
|---|---:|---:|---|
| RMSE NO2 | ≤ 8 ug/m3 | No evaluable | Solo 1 estación |
| RMSE SO2 | ≤ 6 ug/m3 | 5.78 | Cerca/cumple por RMSE reportado |
| RMSE O3 | ≤ 12 ug/m3 | 5.93 | Cumple |
| R2 LOO-CV promedio | ≥ 0.55 | Negativo | No cumple |
| Moran I | > 0.30 | Pendiente | No verificado |

## Limitaciones

- NO2 solo tiene una estación en el parquet principal.
- SO2 y O3 tienen pocas estaciones para LOO-CV robusto.
- ConvLSTM y Ridge no logran R2 positivos.
- Kriging funciona mejor, pero con baja capacidad para explicar varianza.
- Moran I queda pendiente si no se calcula explícitamente.

## Lectura final

Situación 3 debe reportarse con honestidad: Kriging da errores absolutos razonables para SO2 y O3, pero no se alcanza una validación predictiva fuerte para todos los KPIs.

## Referencias

- [Kriging y LOO-CV](kriging-loocv.md)
- [ConvLSTM](convlstm.md)
- [Resultados Situación 3 original](../SIT3_RESULTADOS.md)
- [PySAL esda stable documentation](https://pysal.org/esda/stable/)
