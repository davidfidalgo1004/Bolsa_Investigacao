import random
import numpy as np

import dash
from dash import Dash, html, dcc, Output, Input, State, ctx
import plotly.graph_objects as go

# --- Importa lógica do simulador ---
from Environment.ambiente import EnvironmentModel
from components.settings.MapColor import EncontrarCor

# Dash-Leaflet para mapa interactivo
import dash_leaflet as dl
# Suporte para diferenças de versão — tenta DrawControl, senão EditControl
try:
    from dash_leaflet import DrawControl  # >=0.1.17
except ImportError:
    from dash_leaflet import EditControl as DrawControl  # >=1.1
from dash.exceptions import PreventUpdate
import json


# ----------------- Configurações -----------------
WORLD_W = 125
WORLD_H = 108
CELL_SIZE = 5  # apenas para consistência com desktop

# Bounding box de Portugal Continental (lon_min, lon_max, lat_min, lat_max)
PORTUGAL_BOUNDS = (-9.56, -6.18, 36.96, 42.18)


# ----------------- Estado global -----------------
class SimState:
    """Guarda o estado da simulação para ser acedido pelos callbacks Dash."""

    def __init__(self):
        self.running = False
        self.model: EnvironmentModel | None = None
        self.burned = []
        self.forested = []
        self.timesteps = []
        self.iteration = 0
        self.total_iters = 100  # default
        # Usa Portugal Continental como área padrão
        self.bounds = PORTUGAL_BOUNDS

    def setup_model(self, density=0.5):
        """Cria um novo EnvironmentModel com os parâmetros indicados."""
        self.model = EnvironmentModel(
            WORLD_W, WORLD_H, density=density, env_type="only_trees"
        )
        # Limpa séries
        self.burned.clear()
        self.forested.clear()
        self.timesteps.clear()
        self.iteration = 0

    def step(self):
        """Executa um passo da simulação e actualiza as métricas."""
        if not self.model:
            return
        self.model.step()
        # Métricas
        burned = sum(
            1 for a in self.model.schedule if getattr(a, "state", None) == "burned"
        )
        forested = sum(
            1 for a in self.model.schedule if getattr(a, "state", None) == "forested"
        )
        self.burned.append(burned)
        self.forested.append(forested)
        self.timesteps.append(self.iteration)
        self.iteration += 1

    def set_geojson(self, geojson_dict):
        """Define limites a partir de um GeoJSON e devolve bounding box (min_lon,max_lon,min_lat,max_lat)."""
        self.geojson = geojson_dict
        lons = []
        lats = []
        def _collect_coords(geom):
            gtype = geom.get("type")
            if gtype == "Polygon":
                return geom.get("coordinates", [[]])[0]
            elif gtype == "MultiPolygon":
                coords = []
                for poly in geom.get("coordinates", []):
                    coords.extend(poly[0])
                return coords
            elif gtype == "LineString":
                return geom.get("coordinates", [])
            elif gtype == "MultiLineString":
                coords = []
                for line in geom.get("coordinates", []):
                    coords.extend(line)
                return coords
            return []
        for feat in geojson_dict.get("features", []):
            coords = _collect_coords(feat.get("geometry", {}))
            # Guarda forma shapely se possível
            try:
                from shapely.geometry import shape as _shape
                geom_obj = _shape(feat.get("geometry", {}))
                if not hasattr(self, "_shapes"):
                    self._shapes = []
                self._shapes.append(geom_obj)
            except Exception:
                pass
            for lon, lat in coords:
                lons.append(lon)
                lats.append(lat)
        if lons and lats:
            self.bounds = (min(lons), max(lons), min(lats), max(lats))
        else:
            self.bounds = None

    def grid_to_latlon_color(self):
        """Retorna listas de lat,lon,cores para plot caso GeoJSON esteja definido."""
        if not getattr(self, "bounds", None):
            return None, None, None
        min_lon, max_lon, min_lat, max_lat = self.bounds
        lon_span = max_lon - min_lon or 1e-9
        lat_span = max_lat - min_lat or 1e-9
        lons = []
        lats = []
        colors = []
        for agent in self.model.schedule:
            if hasattr(agent, "pos") and hasattr(agent, "pcolor") and getattr(agent, "state", None) != "forested":
                x, y = agent.pos
                lon = min_lon + (x / (WORLD_W - 1)) * lon_span
                lat = max_lat - (y / (WORLD_H - 1)) * lat_span
                # Verifica se ponto está dentro do polígono (caso definido)
                inside = True
                if hasattr(self, "_shapes"):
                    try:
                        from shapely.geometry import Point as _Pt
                        inside = any(shp.contains(_Pt(lon, lat)) for shp in self._shapes)
                    except Exception:
                        pass
                if inside:
                    lons.append(lon)
                    lats.append(lat)
                    colors.append(EncontrarCor(agent.pcolor))
        return lats, lons, colors

    # ---------- Helpers ----------
    def grid_to_matrix(self):
        """Converte o pcolor da grelha para matriz (H x W) de hex-strings cor."""
        mat = np.zeros((WORLD_H, WORLD_W), dtype=object)
        for agent in self.model.schedule:
            if hasattr(agent, "pos") and hasattr(agent, "pcolor"):
                x, y = agent.pos
                mat[y, x] = EncontrarCor(agent.pcolor)
        return mat

    # ---------- Ignite helpers ----------
    def latlon_to_grid(self, lat: float, lon: float):
        """Converte coordenadas lat/lon para índices (x,y) da grelha."""
        if not getattr(self, "bounds", None):
            return None
        min_lon, max_lon, min_lat, max_lat = self.bounds
        lon_span = max_lon - min_lon or 1e-9
        lat_span = max_lat - min_lat or 1e-9
        x = int(round(((lon - min_lon) / lon_span) * (WORLD_W - 1)))
        y = int(round(((max_lat - lat) / lat_span) * (WORLD_H - 1)))
        x = max(0, min(WORLD_W - 1, x))
        y = max(0, min(WORLD_H - 1, y))
        return x, y

    def ignite_at(self, lat: float, lon: float):
        """Inicia fogo na posição lat/lon se possível."""
        if not self.model:
            return False
        grid_coords = self.latlon_to_grid(lat, lon)
        if not grid_coords:
            return False
        x, y = grid_coords
        return self.model.start_fire_at(x, y)

    def grid_to_png_image(self):
        """Gera imagem RGBA (base64) da grelha actual limitada ao polígono."""
        if not getattr(self, "bounds", None):
            return None, None
        from PIL import Image
        # Gera matriz de cores (hex) filtrada
        lats, lons, colors = self.grid_to_latlon_color()
        if not lats:
            return None, None
        # Criar imagem vazia
        img = Image.new("RGBA", (WORLD_W, WORLD_H), (0, 0, 0, 0))
        for lat, lon, color in zip(lats, lons, colors):
            # converter lat/lon para x,y indice
            x, y = self.latlon_to_grid(lat, lon)
            if x is None:
                continue
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            img.putpixel((x, y), (r, g, b, 180))  # alpha semi
        # Redimensiona para resoluçao maior para suavizar
        upscale = 4
        img = img.resize((WORLD_W*upscale, WORLD_H*upscale), Image.NEAREST)
        # Codifica base64 png
        import io, base64
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        return f"data:image/png;base64,{b64}", self.bounds


STATE = SimState()

# ----------------- Dash App -----------------
app: Dash = dash.Dash(__name__)
server = app.server  # para deployment WSGI

# Layout
app.layout = html.Div(
    [
        html.H2("Simulador de Incêndio – Interface Web"),
        html.Div(
            [
                html.Button("Setup", id="btn-setup", n_clicks=0),
                html.Button("Iniciar", id="btn-start", n_clicks=0, disabled=True),
                html.Button("Pausar", id="btn-pause", n_clicks=0, disabled=True),
            ]
        ),
        html.Div([
            dl.Map(center=[39.5, -8.0], zoom=6, children=[
                dl.TileLayer(url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"),
                dl.FeatureGroup([DrawControl(id="draw-control")], id="feature-group"),
                # Camada para desenhar o estado da simulação (actualiza a cada passo)
                dl.LayerGroup(id="sim-layer"),
                dl.ImageOverlay(id="sim-img", url="", bounds=[[0, 0], [0, 0]]),
            ], id="leaflet-map", style={"width": "100%", "height": "500px"}),
        ]),
        dcc.Store(id="geojson-store"),
        dcc.Graph(id="burn-graph"),
        # Interval dispara a cada 500 ms quando running=True
        dcc.Interval(id="sim-interval", interval=500, n_intervals=0, disabled=True),
        html.Button("Calcular Risco (API)", id="btn-risk", n_clicks=0, disabled=True),
        html.Div(id="risk-output"),
        html.Div(id="ignite-status"),
    ],
    style={"maxWidth": "1100px", "margin": "auto"},
)


# ----------------- Callbacks -----------------
@app.callback(
    Output("btn-start", "disabled"),
    Output("btn-pause", "disabled"),
    Output("sim-interval", "disabled"),
    Input("btn-start", "n_clicks"),
    Input("btn-pause", "n_clicks"),
    State("sim-interval", "disabled"),
    prevent_initial_call=True,
)
def control_sim(start_clicks, pause_clicks, interval_disabled):
    """Inicia ou pausa a simulação conforme botão pressionado."""
    triggered = ctx.triggered_id
    if triggered == "btn-start":
        STATE.running = True
        return False, False, False  # start habilitado=False, pause habilitado=False? Wait.
    elif triggered == "btn-pause":
        STATE.running = False
        return False, True, True  # start enabled, pause disabled, interval disabled
    return not STATE.running, not STATE.running, not STATE.running


@app.callback(
    Output("burn-graph", "figure"),
    Output("sim-img", "url"),
    Output("sim-img", "bounds"),
    Input("sim-interval", "n_intervals"),
)
def update_sim_outputs(n):
    """Actualiza gráfico e camada de mapa a cada passo de simulação."""
    # Avança simulação se estiver a correr
    if STATE.running and STATE.model:
        STATE.step()

    # --- Gráfico ---
    if not STATE.model:
        fig = go.Figure()
    else:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=STATE.timesteps, y=STATE.burned, mode="lines", name="Queimadas", line=dict(color="firebrick")))
        fig.add_trace(go.Scatter(x=STATE.timesteps, y=STATE.forested, mode="lines", name="Florestadas", line=dict(color="green")))
        fig.update_layout(margin=dict(l=40, r=20, t=30, b=30))

    # --- Imagem sobreposta ---
    img_url, bounds = STATE.grid_to_png_image()
    if img_url is None:
        return fig, dash.no_update, dash.no_update
    return fig, img_url, [[bounds[2], bounds[0]], [bounds[3], bounds[1]]]  # [[southWestLat, southWestLon],[northEastLat,northEastLon]]


@app.callback(
    Output("geojson-store", "data"),
    Output("btn-risk", "disabled"),
    Input("draw-control", "geojson"),
)
def capture_geojson(feature_coll):
    if not feature_coll or not feature_coll.get("features"):
        return dash.no_update, True
    # Guarda limites para projectar grelha -> lat/lon
    STATE.set_geojson(feature_coll)
    return feature_coll, False


@app.callback(
    Output("risk-output", "children"),
    Input("btn-risk", "n_clicks"),
    State("geojson-store", "data"),
    prevent_initial_call=True,
)
def call_api(n_clicks, geojson_data):
    if not geojson_data:
        raise PreventUpdate
    # Chama a mesma função _calculate_risk_api que existe no desktop (reutilizamos)
    from main import BASE_URL, HEADERS  # reutiliza tokens
    try:
        import requests
        resp = requests.post(f"{BASE_URL}/calculate-risk/", headers=HEADERS, json=geojson_data, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        return f"Risco calculado com sucesso: {result}"
    except Exception as e:
        return f"Erro ao contactar API: {e}"


@app.callback(
    Output("btn-start", "disabled", allow_duplicate=True),
    Output("btn-pause", "disabled", allow_duplicate=True),
    Input("btn-setup", "n_clicks"),
    prevent_initial_call=True,
)
def setup_click(n):
    """Cria um modelo novo."""
    STATE.setup_model(density=0.5)
    STATE.running = False
    return False, True  # start enabled, pause disabled


@app.callback(
    Output("ignite-status", "children"),
    Input("leaflet-map", "click_lat_lng"),
    State("geojson-store", "data"),
    prevent_initial_call=True,
)
def ignite_on_click(lat_lng, geojson_data):
    """Inicia incêndio na posição clicada se estiver dentro da área desenhada."""
    if not lat_lng or not geojson_data:
        raise PreventUpdate
    lat, lon = lat_lng  # dash-leaflet devolve [lat, lon]
    success = STATE.ignite_at(lat, lon)
    if success:
        STATE.running = True  # inicia simulação imediatamente
        return f"Incêndio iniciado em ({lat:.4f}, {lon:.4f})"
    return "Clique numa célula florestada para iniciar incêndio."


# ----------------- Execução -----------------
if __name__ == "__main__":
    STATE.setup_model()
    app.run(debug=True) 