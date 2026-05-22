# ConvLSTM

## Qué contiene

Resultados del modelo ConvLSTM entrenado sobre secuencias de embeddings.

## Configuración

- Arquitectura: 2 capas.
- Hidden size: 128.
- Kernel: 3.
- Secuencias potenciales: 2,839.

## Resultado

| Epoch | Loss |
|---|---:|
| 1 | 0.9105 |
| 5 | 0.6170 |
| 10 | 0.5927 |

El modelo converge en pérdida, pero no logra R2 positivos en LOO-CV.

## Lectura

Los embeddings CLIP aprendidos en Situación 2 son útiles para clasificación, pero no bastan para predecir concentraciones absolutas en estaciones no vistas.

## Referencias

- [ConvLSTM, Kriging y LOO-CV](../metodologia/convlstm-kriging-loocv.md)
- [Resultados Situación 3 original](../SIT3_RESULTADOS.md)
- [ConvLSTM paper](https://arxiv.org/abs/1506.04214)
