# -*- coding: utf-8 -*-
import json
import time
import datetime
import streamlit as st
import paho.mqtt.client as mqtt

# =============================
# Configuración de página
# =============================
st.set_page_config(
    page_title="MQTT Sensor Reader · Tech Mode",
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
    --bg:#0b1220;        /* fondo */
    --panel:#0f182b;     /* tarjetas */
    --text:#e6f7ff;      /* texto */
    --muted:#9fb3c8;     /* texto secundario */
    --accent:#00e5ff;    /* cian */
    --accent2:#00ffa3;   /* verde */
  }
  html, body, .stApp{
    background: radial-gradient(1000px 600px at 10% 0%, #0f1a30 0%, var(--bg) 60%);
    color: var(--text) !important;
  }
  [data-testid="stSidebar"]{
    background: linear-gradient(180deg, #0e1628 0%, #091021 100%) !important;
    border-right: 1px solid rgba(0,229,255,.15);
  }
  h1,h2,h3,h4,h5,h6{
    color: var(--accent);
    font-family: "JetBrains Mono", monospace;
    letter-spacing:.35px;
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
  .stButton>button:hover{
    transform: translateY(-1px);
    box-shadow:0 0 20px rgba(0,229,255,.55);
  }
  .badge{
    display:inline-block; padding:4px 10px; border-radius:999px;
    background: rgba(0,229,255,.12); color: var(--accent);
    border:1px solid rgba(0,229,255,.35); font-size:12px; margin-left:6px;
  }
  .badge.bad{
    background: rgba(255,77,79,.08); color: #ffb3b4; border:1px solid rgba(255,77,79,.35);
  }
</style>
""", unsafe_allow_html=True)

# =============================
# Estado
# =============================
if "sensor_data" not in st.session_state:
    st.session_state.sensor_data = None
if "last_update" not in st.session_state:
    st.session_state.last_update = None

# =============================
# MQTT (lectura con timeout)
# =============================
def get_mqtt_message(broker, port, topic, client_id, timeout_s=5):
    """
    Se suscribe al tópico y espera un mensaje (máx timeout_s seg).
    Devuelve payload (dict o texto) o dict con 'error'.
    """
    message_received = {"received": False, "payload": None}

    def on_message(client, userdata, message):
        try:
            payload = json.loads(message.payload.decode())
        except Exception:
            payload = message.payload.decode(errors="ignore")
        message_received["payload"] = payload
        message_received["received"] = True

    try:
        client = mqtt.Client(client_id=client_id)
        client.on_message = on_message
        client.connect(broker, port, 60)
        client.subscribe(topic)
        client.loop_start()

        t_end = time.time() + timeout_s
        while not message_received["received"] and time.time() < t_end:
            time.sleep(0.08)

        client.loop_stop()
        client.disconnect()
        return message_received["payload"]
    except Exception as e:
        return {"error": str(e)}

# =============================
# Sidebar — Config
# =============================
with st.sidebar:
    st.subheader("⚙️ Conexión MQTT")
    broker = st.text_input("Broker", value="broker.mqttdashboard.com", help="Servidor MQTT")
    port = st.number_input("Puerto", value=1883, min_value=1, max_value=65535, step=1)
    topic = st.text_input("Tópico", value="sensor_st", help="Tópico a suscribirse")
    client_id = st.text_input("Client ID", value="streamlit_client", help="Identificador único")
    st.markdown("---")
    auto_refresh = st.toggle("Auto-refresh (cada 3s)", value=False)
    st.caption("Si está activo, la app reintenta lectura periódica (pull puntual).")

# =============================
# Header
# =============================
st.title("📡 MQTT Sensor Reader — Tech Mode")
colA, colB = st.columns([2,1])
with colA:
    st.markdown("Monitoreo minimalista de sensores vía **MQTT** con **UI dark-neón**.")
with colB:
    st.markdown(f"Estado: <span class='badge'>ID: {client_id}</span>", unsafe_allow_html=True)

with st.expander("ℹ️ Tips rápidos"):
    st.markdown("""
- Verifica **broker**, **puerto** y **tópico** en el panel lateral.  
- Pulsa **Obtener Datos** para leer el último mensaje.  
- Si el payload es **JSON**, verás métricas por campo y el objeto completo.  
- Brokers públicos útiles: `broker.mqttdashboard.com`, `test.mosquitto.org`, `broker.hivemq.com`.
""")

st.divider()

# =============================
# Acciones
# =============================
btn = st.button("🔄 Obtener Datos del Sensor", use_container_width=True)

if btn or auto_refresh:
    with st.spinner("Conectando al broker y esperando datos..."):
        data = get_mqtt_message(broker, int(port), topic, client_id)
        st.session_state.sensor_data = data
        st.session_state.last_update = datetime.datetime.now()

# =============================
# Resultados
# =============================
if st.session_state.sensor_data:
    st.divider()
    last_ts = st.session_state.last_update.strftime("%Y-%m-%d %H:%M:%S") if st.session_state.last_update else "—"
    ok = not (isinstance(st.session_state.sensor_data, dict) and "error" in st.session_state.sensor_data)
    badge = "<span class='badge'>OK</span>" if ok else "<span class='badge bad'>ERROR</span>"
    st.subheader(f"📊 Datos Recibidos {badge}")
    st.caption(f"Última actualización: {last_ts}")

    data = st.session_state.sensor_data

    if isinstance(data, dict) and "error" in data:
        st.error(f"❌ Error de conexión: {data['error']}")
    else:
        st.success("✅ Datos recibidos correctamente")
        if isinstance(data, dict):
            # Métricas responsivas por clave
            keys = list(data.keys())
            if keys:
                cols = st.columns(min(4, len(keys)))
                for i, k in enumerate(keys):
                    with cols[i % len(cols)]:
                        st.metric(label=str(k), value=str(data[k]))
            with st.expander("🧾 Ver JSON completo"):
                st.json(data)
        else:
            st.markdown("**Payload (texto):**")
            st.code(str(data))
else:
    st.info("Aún no hay datos. Ajusta la conexión y pulsa **Obtener Datos del Sensor**.")
