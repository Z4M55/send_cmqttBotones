# -*- coding: utf-8 -*-
import json
import time
import datetime
import platform
import streamlit as st
import paho.mqtt.client as paho

# =============================
# Configuración de página
# =============================
st.set_page_config(
    page_title="MQTT Control · Tech Mode",
    page_icon="🛰️",
    layout="centered",
    initial_sidebar_state="expanded"
)

# =============================
# Estilos (dark + neón)
# =============================
st.markdown("""
<style>
  :root{
    --bg:#0b1220;
    --panel:#0f182b;
    --text:#e6f7ff;
    --muted:#9fb3c8;
    --accent:#00e5ff;
    --accent2:#00ffa3;
  }
  html, body, .stApp{
    background: radial-gradient(1000px 600px at 10% 0%, #0f1a30 0%, var(--bg) 60%);
    color: var(--text) !important;
  }
  [data-testid="stSidebar"]{
    background: linear-gradient(180deg,#0e1628 0%,#091021 100%) !important;
    border-right: 1px solid rgba(0,229,255,.15);
  }
  h1,h2,h3,h4,h5,h6{
    color: var(--accent);
    font-family: "JetBrains Mono", monospace;
    letter-spacing: .4px;
  }
  p, label, span, .stMarkdown{
    color: var(--text) !important;
    font-family: "Inter", system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
  }
  .stButton>button{
    width: 100%;
    background: linear-gradient(90deg, var(--accent) 0%, var(--accent2) 100%) !important;
    color:#00121a !important;
    border:none !important;
    border-radius:12px !important;
    font-weight:700 !important;
    box-shadow:0 0 14px rgba(0,229,255,.35);
    transition: transform .08s ease-in-out, box-shadow .2s ease-in-out;
  }
  .stButton>button:hover{ transform: translateY(-1px); box-shadow:0 0 20px rgba(0,229,255,.55); }
  .badge{
    display:inline-block; padding:4px 10px; border-radius:999px;
    background: rgba(0,229,255,.12); color: var(--accent);
    border:1px solid rgba(0,229,255,.35); font-size:12px; margin-left:6px;
  }
  .badge.bad{
    background: rgba(255,77,79,.10); color: #ffb3b4; border:1px solid rgba(255,77,79,.35);
  }
  .muted{ color: var(--muted) !important; font-size: 13px; }
</style>
""", unsafe_allow_html=True)

# =============================
# Estado
# =============================
if "last_pub" not in st.session_state:
    st.session_state.last_pub = None
if "last_status" not in st.session_state:
    st.session_state.last_status = "—"
if "last_payload" not in st.session_state:
    st.session_state.last_payload = None

# =============================
# Funciones MQTT
# =============================
def publish_mqtt(broker: str, port: int, client_id: str, topic: str, payload: dict, qos: int = 0, retain: bool = False):
    """Publica un mensaje MQTT y devuelve (ok, error|None)."""
    try:
        client = paho.Client(client_id=client_id)
        client.connect(broker, port, 60)
        res = client.publish(topic, json.dumps(payload), qos=qos, retain=retain)
        res.wait_for_publish()
        client.disconnect()
        return True, None
    except Exception as e:
        return False, str(e)

# =============================
# Sidebar — Configuración
# =============================
with st.sidebar:
    st.subheader("⚙️ Conexión")
    broker = st.text_input("Broker", value="157.230.214.127")
    port = st.number_input("Puerto", value=1883, min_value=1, max_value=65535, step=1)
    client_id = st.text_input("Client ID", value="GIT-HUB")

    st.subheader("📡 Tópicos")
    topic_switch = st.text_input("Tópico ON/OFF", value="cmqtt_s")
    topic_analog = st.text_input("Tópico Analógico", value="cmqtt_a")

# =============================
# Header
# =============================
st.title("🛰️ MQTT Control — Tech Mode")
st.caption(f"💻 Python: `{platform.python_version()}` • Broker: `{broker}` • Puerto: `{port}`")

st.divider()

# =============================
# Controles ON/OFF
# =============================
st.subheader("🔌 Salida Digital (Act1)")
col1, col2 = st.columns(2, gap="large")

with col1:
    if st.button("ON", use_container_width=True):
        payload = {"Act1": "ON"}
        ok, err = publish_mqtt(broker, int(port), client_id, topic_switch, payload)
        st.session_state.last_pub = datetime.datetime.now()
        st.session_state.last_status = "OK" if ok else f"ERROR: {err}"
        st.session_state.last_payload = {"topic": topic_switch, "payload": payload}

with col2:
    if st.button("OFF", use_container_width=True):
        payload = {"Act1": "OFF"}
        ok, err = publish_mqtt(broker, int(port), client_id, topic_switch, payload)
        st.session_state.last_pub = datetime.datetime.now()
        st.session_state.last_status = "OK" if ok else f"ERROR: {err}"
        st.session_state.last_payload = {"topic": topic_switch, "payload": payload}

# =============================
# Control analógico
# =============================
st.subheader("🎚️ Salida Analógica")
values = st.slider("Selecciona el valor", 0.0, 100.0, 50.0, 1.0)
if st.button("📤 Enviar valor", use_container_width=True):
    payload = {"Analog": float(values)}
    ok, err = publish_mqtt(broker, int(port), client_id, topic_analog, payload)
    st.session_state.last_pub = datetime.datetime.now()
    st.session_state.last_status = "OK" if ok else f"ERROR: {err}"
    st.session_state.last_payload = {"topic": topic_analog, "payload": payload}

# =============================
# Estado de la última publicación
# =============================
st.divider()
st.subheader("📈 Estado de publicación")
if st.session_state.last_pub:
    ts = st.session_state.last_pub.strftime("%Y-%m-%d %H:%M:%S")
    ok = st.session_state.last_status == "OK"
    badge = "<span class='badge'>OK</span>" if ok else f"<span class='badge bad'>{st.session_state.last_status}</span>"
    st.markdown(f"Resultado: {badge} · <span class='muted'>[{ts}]</span>", unsafe_allow_html=True)

    with st.expander("🧾 Ver payload enviado"):
        st.json(st.session_state.last_payload or {})
else:
    st.info("Aún no has enviado comandos. Usa **ON/OFF** o **Enviar valor**.")

# =============================
# Nota
# =============================
st.markdown(
    "<p class='muted'>Tip: si no ves efecto, verifica que tu dispositivo esté suscrito a los tópicos y alcance el broker.</p>",
    unsafe_allow_html=True
)
