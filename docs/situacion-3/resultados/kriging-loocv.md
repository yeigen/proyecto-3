# Kriging y LOO-CV

## Qué contiene

Resultados de Kriging Ordinario dejando una estación fuera.

## SO2

- Estaciones evaluables: 4.
- MAE: 5.02 ug/m3.
- RMSE aproximado: 5.78 ug/m3.

## O3

- Estaciones evaluables: 7.
- MAE: 4.91 ug/m3.
- RMSE aproximado: 5.93 ug/m3.

## NO2

LOO-CV no es evaluable porque solo Yumbo tiene NO2 en el parquet principal.

## Lectura

Kriging Ordinario fue la alternativa más útil frente a ConvLSTM y Ridge. El R2 sigue siendo bajo o negativo, pero MAE/RMSE son más interpretables con pocas estaciones.

## Referencias

- [ConvLSTM, Kriging y LOO-CV](../metodologia/convlstm-kriging-loocv.md)
- [Resultados Situación 3 original](../SIT3_RESULTADOS.md)
- [Kriging — PyKrige](https://geostat-framework.readthedocs.io/projects/pykrige/en/stable/)
