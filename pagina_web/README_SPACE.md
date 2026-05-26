---
title: GeoVision CLIP Cali
emoji: 🛰️
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
license: cc0-1.0
---

# GeoVision-CLIP Cali — Estimación de contaminación atmosférica

Sistema de estimación de NO₂, SO₂ y O₃ en Santiago de Cali mediante Deep Learning (CLIP + Sparse Autoencoders sobre Sentinel-2/5P) + Kriging Espacio-Temporal.

## Stack
- **Backend**: FastAPI sirviendo la malla de inferencia ConvLSTM + ST-Kriging pre-computada
- **Frontend**: React + Vite + Leaflet (mapa interactivo de Cali)

## Uso
- Mapa interactivo con las 9 estaciones DAGMA georreferenciadas
- Selección de contaminante (SO₂, O₃) y horizonte temporal (T+1, T+3, T+7)
- Mapas de gradiente + capa de incertidumbre (σ Kriging)
- Click en cualquier punto → predicción valor ± σ
- Descarga de predicciones en CSV

## Nota
NO₂ no tiene mapa de Kriging: solo 2 estaciones DAGMA lo miden (insuficiente para variograma, n≥3).

Universidad Autónoma de Occidente · Analítica de Datos I · 2026
