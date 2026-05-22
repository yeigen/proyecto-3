# Arquitectura CLIP + SAE

## Qué contiene

Arquitectura del modelo multimodal usado en Situación 2 y análisis posterior de embeddings.

## CLIP final

El modelo final usa RemoteCLIP ViT-B/32 con LoRA. La rama con valores S5P fue eliminada para evitar data leakage.

| Componente | Decisión |
|---|---|
| Encoder visual | RemoteCLIP ViT-B/32 |
| Encoder textual | RemoteCLIP text encoder |
| Fine-tuning | LoRA rank 16 |
| Entrada visual | Bandas ópticas Sentinel-2 |
| Rama S5P | Eliminada |
| Aumentos | Flip horizontal y rotaciones 0/90/180/270 |

## SAE

Sparse Autoencoder entrenado sobre embeddings de 512 dimensiones:

```text
Linear(512, 256) + ReLU + Linear(256, 512)
```

## Referencias

- [CLIP paper](https://arxiv.org/abs/2103.00020)
- [RemoteCLIP paper](https://ieeexplore.ieee.org/document/10504785)
- [RemoteCLIP en Hugging Face](https://huggingface.co/chendelong/RemoteCLIP)
- [LoRA paper](https://arxiv.org/abs/2106.09685)
- [CLIP + SAE Sit 2 original](../SIT2_CLIP_SAE.md)
- [Concepto CLIP y RemoteCLIP](../../conceptos/clip-y-remoteclip.md)
