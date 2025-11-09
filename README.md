# software-factory-chicken

Prototipo de **visualización en tiempo (casi) real** para conteo de pollos.

---

## ⚙️ Requisitos / Entorno

### Opción Conda (recomendada)

```bash
conda create -n sfc python=3.12 -y
conda activate sfc
conda install -c conda-forge streamlit pandas numpy pillow opencv ffmpeg -y
# (si falta algo)
pip install opencv-python-headless
```
---

## ▶️ Ejecutar la app

```bash
streamlit run app.py
```

---

### `requirements.txt`

```
streamlit==1.51.0
pandas>=2.0
numpy>=1.26
Pillow
opencv-python-headless
```

### `environment.yml`

```yaml
name: sfc
channels:
  - conda-forge
dependencies:
  - python=3.12
  - streamlit
  - pandas
  - numpy
  - pillow
  - opencv
  - ffmpeg
  - pip
  - pip:
      - opencv-python-headless
```


---

## 🧩 Issues sugeridos

1. **Play/Pause/Reset + estado**
2. **Barra de progreso + ETA**
3. **Validación de duración/formato** (≤60 s, .mp4)
4. **Tabs y layout final** (vistas + métricas + descargas)
5. **Generador desacoplado** (`generators.py`) con contrato estable
6. **Overlay heatmap (helper)** y zonas 3×3 (métrica)
7. **Export de sesión** (`metrics_session.csv`, `zones.csv`, `summary.json`)
8. **Manejo de errores/edge cases** (video corrupto, sin códec, etc.)


---

## ✅ Definition of Done (MVP UI)

* 3 paneles sincronizados (Original/A1/A2) con controles.
* Métricas vivas: Conteo A1, Conteo A2, Congestión%, Latencia, FPS + gráfico temporal.
* Validaciones y mensajes claros.
* Export de sesión funcionando.
