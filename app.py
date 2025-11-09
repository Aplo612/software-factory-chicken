# app.py
import streamlit as st
import pandas as pd
import numpy as np
import time, io, cv2, pathlib
from PIL import Image, ImageDraw

st.set_page_config(page_title="DFCCNet Demo Live", layout="wide")
st.title("Conteo de Pollos – Vista en vivo (Original vs Alg1 vs Alg2)")

ROOT = pathlib.Path(__file__).parent
TMP = ROOT / "tmp"; TMP.mkdir(exist_ok=True)

# --------- Stub de procesamiento (reemplaza por tu generador) ----------
def stub_generator(video_path:str, max_frames:int=400, target_fps:float=10.0):
    """Lee video y rinde 3 imágenes + métricas por frame."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError("No pude abrir el video.")
    # downsample fps
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 25
    step = max(int(round(src_fps / target_fps)), 1)

    frame_idx = 0
    out_idx = 0
    last_time = time.perf_counter()

    while True:
        ret, frame = cap.read()
        if not ret: break
        if frame_idx % step != 0:
            frame_idx += 1
            continue

        t0 = time.perf_counter()
        # Resize para UI
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (720, int(720 * frame.shape[0]/frame.shape[1])))
        pil_orig = Image.fromarray(frame)

        # Simular Alg1/Alg2 con overlays
        pil_a1 = pil_orig.copy()
        pil_a2 = pil_orig.copy()
        draw1 = ImageDraw.Draw(pil_a1); draw2 = ImageDraw.Draw(pil_a2)

        # “zonas calientes” falsas
        x = 40 + (out_idx*15) % 300
        draw1.rectangle([x, 60, x+160, 160], outline=(255,80,80), width=3)
        draw2.ellipse([x+50, 90, x+200, 210], outline=(80,200,255), width=3)

        # Conteos “simulados”
        count1 = int(100 + 15*np.sin(out_idx/7))
        count2 = int(100 + 10*np.sin(out_idx/9 + 0.7))
        # Congestión “simulada” (% área alta densidad)
        congestion = max(0.0, 20 + 15*np.sin(out_idx/11))

        # Actividad: diferencia simple vs frame anterior (simulada)
        now = time.perf_counter()
        infer_ms = (now - t0) * 1000
        model_fps = 1000.0 / max(infer_ms, 1e-3)

        # Serializamos imágenes a bytes para streamlit
        def to_bytes(pil_img):
            buf = io.BytesIO()
            pil_img.save(buf, format="PNG")
            return buf.getvalue()

        yield {
            "t": out_idx / target_fps,
            "orig": to_bytes(pil_orig),
            "a1": to_bytes(pil_a1),
            "a2": to_bytes(pil_a2),
            "count1": count1,
            "count2": count2,
            "congestion": float(congestion),
            "infer_ms": float(infer_ms),
            "model_fps": float(model_fps),
        }

        out_idx += 1
        frame_idx += 1
        if out_idx >= max_frames: break

    cap.release()

# ------------------- UI -------------------
left, right = st.columns([2,1])
with left:
    uploaded = st.file_uploader("Sube un video (.mp4, ≤60s)", type=["mp4"])
with right:
    target_fps = st.slider("FPS de procesamiento", 5, 20, 10)
    max_frames = st.slider("Máx. frames a mostrar", 100, 1200, 600, step=50)

start = st.button("▶ Iniciar visualización")

if start:
    if not uploaded:
        st.warning("Sube un .mp4 primero.")
        st.stop()

    # Guardar a disco para OpenCV
    video_path = (TMP / "input.mp4")
    video_path.write_bytes(uploaded.read())

    st.markdown("### Vistas")
    c1, c2, c3 = st.columns(3)
    ph_orig = c1.empty()
    ph_a1   = c2.empty()
    ph_a2   = c3.empty()

    st.markdown("### Métricas en vivo")
    m1, m2, m3, m4, m5 = st.columns(5)
    chart_placeholder = st.empty()

    # Buffers para series
    times, counts1, counts2, congest, lat_ms = [], [], [], [], []

    # Generador (reemplaza por el tuyo)
    gen = stub_generator(str(video_path), max_frames=max_frames, target_fps=target_fps)

    # Bucle “casi real-time”
    start_t = time.perf_counter()
    for pkt in gen:
        # Actualizar imágenes
        ph_orig.image(pkt["orig"], caption=f"Original (t={pkt['t']:.1f}s)", use_container_width=True)
        ph_a1.image(pkt["a1"], caption=f"Algoritmo 1 (t={pkt['t']:.1f}s)", use_container_width=True)
        ph_a2.image(pkt["a2"], caption=f"Algoritmo 2 (t={pkt['t']:.1f}s)", use_container_width=True)

        # Actualizar métricas
        times.append(pkt["t"])
        counts1.append(pkt["count1"])
        counts2.append(pkt["count2"])
        congest.append(pkt["congestion"])
        lat_ms.append(pkt["infer_ms"])

        m1.metric("Conteo A1", counts1[-1])
        m2.metric("Conteo A2", counts2[-1])
        m3.metric("Congestión (%)", f"{congest[-1]:.1f}")
        m4.metric("Latencia (ms)", f"{np.mean(lat_ms[-30:]):.0f}")
        m5.metric("FPS modelo", f"{pkt['model_fps']:.1f}")

        # Serie de tiempo (sliding window)
        df = pd.DataFrame({
            "t": times[-300:],
            "A1": counts1[-300:],
            "A2": counts2[-300:],
            "Congestión": congest[-300:],
        }).set_index("t")
        chart_placeholder.line_chart(df)

        # Ritmo de visualización (best-effort)
        time.sleep(1.0/target_fps)

    # Exportar CSV de la sesión
    out_df = pd.DataFrame({
        "t": times, "count_a1": counts1, "count_a2": counts2,
        "congestion_pct": congest, "latency_ms": lat_ms
    })
    csv_bytes = out_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇ Descargar CSV (sesión)", data=csv_bytes, file_name="metrics_session.csv", mime="text/csv")

    st.success("Fin de la visualización.")
else:
    st.info("Sube un .mp4 y presiona **Iniciar visualización**. Verás 3 paneles sincronizados + métricas vivas.")
