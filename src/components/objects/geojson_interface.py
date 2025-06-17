import os
import streamlit as st
from streamlit_folium import st_folium
import folium
import requests

from components.settings.geradorAPIs import generate_token

# -------------------- Config --------------------
BASE_URL = os.getenv("WILDFIRE_API_BASE_URL", "http://ken01.utad.pt:8080")
AUDIENCE = os.getenv("WILDFIRE_API_AUDIENCE", "ken01.utad.pt:8080")
TOKEN = os.getenv("WILDFIRE_API_TOKEN") or generate_token(AUDIENCE)

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

st.set_page_config(page_title="Wildfire Risk", layout="wide")
st.title("🔶 Desenhar Área & Calcular Risco de Incêndio")

with st.expander("Instruções", expanded=True):
    st.markdown(
        "1. Amplie o mapa até à zona pretendida.\n"
        "2. Clique no ícone de polígono (🖋️).\n"
        "3. Desenhe o contorno da área.\n"
        "4. Clique em **Submit** para enviar e calcular o risco."
    )

# Folium map
m = folium.Map(location=[39.5, -8.0], zoom_start=6, control_scale=True)
folium.TileLayer("OpenStreetMap", name="Mapa base").add_to(m)

# Add draw plugin
from folium.plugins import Draw
Draw(export=True, filename="area.geojson").add_to(m)

output = st_folium(m, width=900, height=600)

drawn_features = output.get("all_drawings", [])

if drawn_features:
    geojson = {
        "type": "FeatureCollection",
        "features": drawn_features,
    }
    st.subheader("GeoJSON gerado")
    st.json(geojson)

    if st.button("Calcular risco", type="primary"):
        try:
            resp = requests.post(
                f"{BASE_URL}/calculate-risk/", headers=HEADERS, json=geojson
            )
            resp.raise_for_status()
            st.success("✅ Risco calculado com sucesso")
            st.json(resp.json())
        except requests.HTTPError as err:
            st.error(f"Erro {err.response.status_code}: {err.response.text}")
else:
    st.info("Desenhe um polígono no mapa para prosseguir.") 