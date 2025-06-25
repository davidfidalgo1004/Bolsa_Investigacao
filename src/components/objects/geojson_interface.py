import os
import streamlit as st
from streamlit_folium import st_folium
import folium
import requests
from pathlib import Path
import re

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
st.title(" Desenhar Área & Calcular Risco de Incêndio")

with st.expander("Instruções", expanded=True):
    st.markdown(
        "1. Amplie o mapa até à zona pretendida.\n"
        "2. Clique no ícone de polígono (🖋️).\n"
        "3. Desenhe o contorno da área.\n"
        "4. Clique em **Submit** para enviar e calcular o risco."
    )

# -------------------- NEW: Pesquisar por coordenadas --------------------
# Guarda centro padrão na sessão se ainda não existir
if "center" not in st.session_state:
    st.session_state["center"] = [39.5, -8.0]

with st.expander("Pesquisar por coordenadas"):
    col_lat, col_lon, col_btn = st.columns([1, 1, 1])
    with col_lat:
        lat_val = st.number_input(
            "Latitude",
            value=st.session_state["center"][0],
            format="%.6f",
            key="lat_input",
        )
    with col_lon:
        lon_val = st.number_input(
            "Longitude",
            value=st.session_state["center"][1],
            format="%.6f",
            key="lon_input",
        )
    with col_btn:
        if st.button("Ir para localização", type="primary"):
            st.session_state["center"] = [lat_val, lon_val]

center = st.session_state["center"]

# Folium map
m = folium.Map(location=center, zoom_start=6, control_scale=True)
# Adiciona marcador caso o utilizador tenha pesquisado coordenadas
if center != [39.5, -8.0]:
    folium.Marker(
        location=center,
        tooltip="Coordenadas pesquisadas",
        icon=folium.Icon(color="red", icon="search"),
    ).add_to(m)

# Camadas de fundo para melhor interpretação do terreno
folium.TileLayer("OpenStreetMap", name="Mapa base").add_to(m)
folium.TileLayer(
    tiles="Stamen Terrain",
    attr="Map tiles by Stamen Design, CC BY 3.0 — Map data © OpenStreetMap contributors",
    name="Terreno",
).add_to(m)
folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="Esri",
    name="Satélite (Esri)",
    overlay=False,
    control=True,
).add_to(m)

# Controlos de camadas
folium.LayerControl(position="topright", collapsed=False).add_to(m)

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

    # Sugere nome da região e permite escolher pasta
    default_name = suggest_region_name(geojson)
    region_name = st.text_input("Nome do ficheiro:", value=default_name)
    dest_folder = st.text_input("Pasta de destino (servidor)", value="downloads")

    # Função simples de slug
    def _slug(s):
        s = re.sub(r"[^A-Za-z0-9_\-]", "_", s)
        return re.sub(r"_+", "_", s).strip("_") or "area"

    file_name = f"{_slug(region_name)}.geojson"
    server_path = Path(dest_folder)
    server_path.mkdir(parents=True, exist_ok=True)
    full_path = server_path / file_name

    # Botão de download (navegador)
    st.download_button(
        label="📥 Download GeoJSON",
        data=str(geojson).encode("utf-8"),
        file_name=file_name,
        mime="application/geo+json",
    )

    # Guarda também no servidor na pasta escolhida e como 'area.geojson'
    full_path.write_text(str(geojson), encoding="utf-8")
    Path("area.geojson").write_text(str(geojson), encoding="utf-8")
    st.success(f"Arquivo guardado em {full_path}")

    if st.button("Calcular risco", type="primary"):
        try:
            resp = requests.post(
                f"{BASE_URL}/calculate-risk/", headers=HEADERS, json=geojson
            )
            resp.raise_for_status()
            st.success(" Risco calculado com sucesso")
            st.json(resp.json())
        except requests.HTTPError as err:
            st.error(f"Erro {err.response.status_code}: {err.response.text}")
else:
    st.info("Desenhe um polígono no mapa para prosseguir.")

# -------------------- Helper: Reverse geocode centroid --------------------
def suggest_region_name(feature_collection):
    """Returns a place name for the centroid of the first feature using
    Nominatim. Falls back to 'area' if request fails."""
    try:
        import statistics

        # Get first polygon / linestring for centroid
        coords = []
        for feat in feature_collection.get("features", []):
            geom = feat.get("geometry", {})
            if geom.get("type") == "Polygon":
                coords.extend(geom.get("coordinates", [[]])[0])
            elif geom.get("type") == "LineString":
                coords.extend(geom.get("coordinates", []))
        if not coords:
            return "area"
        lons, lats = zip(*coords)
        lon = statistics.mean(lons)
        lat = statistics.mean(lats)
        resp = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lon, "format": "json", "zoom": 10},
            headers={"User-Agent": "wildfire-sim/1.0"},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            display_name = data.get("display_name", "area").split(",")[0]
            return display_name.replace(" ", "_")
    except Exception:
        pass
    return "area" 