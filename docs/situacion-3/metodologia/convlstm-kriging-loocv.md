# ConvLSTM, Kriging y LOO-CV

## Qué contiene

Metodología de evaluación para estimar contaminantes en estaciones no vistas.

## Kriging Ordinario

Se usa Kriging Ordinario sobre coordenadas con variograma exponencial y validación LOO-CV, dejando una estación fuera.

## ConvLSTM

Se entrenó una ConvLSTM con secuencias de embeddings. El modelo converge en pérdida, pero no logra R2 positivos en LOO-CV.

## LOO-CV

Leave-One-Out Cross-Validation se aplica por estación. Esto permite probar extrapolación espacial, pero queda limitado por el número bajo de estaciones.

## Lectura metodológica

El mejor resultado práctico fue Kriging Ordinario sobre coordenadas. Los embeddings CLIP ayudan en clasificación en Situación 2, pero muestran correlación limitada con concentraciones absolutas.

## Referencias

- [Resultados Situación 3 original](../SIT3_RESULTADOS.md)
- [Kriging — PyKrige](https://geostat-framework.readthedocs.io/projects/pykrige/en/stable/)
- [ConvLSTM paper](https://arxiv.org/abs/1506.04214)
- [Notebook ConvLSTM + Kriging](../../../notebooks/sit3/01_convlstm_kriging.ipynb)
- [Notebook Situación 3 ConvLSTM](../../../notebooks/sit3/02_situacion-3-conv-lstm.ipynb)
