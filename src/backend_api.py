from __future__ import annotations

"""FastAPI backend exposing the wildfire simulation via REST + WebSocket.

Este módulo implementa apenas a camada de API / motor de simulação — o front-end
SPA (React, Vue, etc.) deverá consumir estes endpoints.

Principais funcionalidades:
• /setup           – cria novo modelo (aceita densidade opcional).
• /region          – recebe o GeoJSON desenhado pelo utilizador.
• /start & /pause  – comando play / pausa.
• /ignite          – inicia fogo numa lat/lon específica.
• /risk            – chama API externa de cálculo de risco.
• /ws              – WebSocket para streaming de passos da simulação em tempo-real.

Os dados enviados por WebSocket incluem:
    {
        "tick": int,
        "burned": int,
        "forested": int,
        "img": str | null,      # data:image/png;…
        "bounds": [lon_min, lon_max, lat_min, lat_max] | null
    }

Isto permite ao front-end actualizar o mapa (overlay da imagem PNG) e gráfico
em tempo-real.
"""

import asyncio
from typing import List

import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- Importa lógica do simulador ---
from Environment.ambiente import EnvironmentModel
from components.settings.MapColor import EncontrarCor
from Agents.firefighter_agent import FirefighterAgent  # utilizado em ff_evo

# ---------- Config constantes ----------
WORLD_W = 125
WORLD_H = 108
PORTUGAL_BOUNDS = (-9.56, -6.18, 36.96, 42.18)
STEP_DELAY = 0.5  # segundos entre passos quando a simulação está a correr


# ----------------- Estado global -----------------
class SimState:
    """Guarda o estado da simulação para ser acedido pela API/WebSocket."""

    def __init__(self):
        self.running: bool = False
        self.model: EnvironmentModel | None = None
        self.burned: list[int] = []
        self.forested: list[int] = []
        self.timesteps: list[int] = []
        self.iteration: int = 0
        self.total_iters = 100  # default
        self.bounds: tuple[float, float, float, float] | None = PORTUGAL_BOUNDS
        self._shapes: list = []  # shapely shapes da região desenhada

    # ---------- Modelo ----------
    def setup_model(self, density: float = 0.5):
        """Cria um novo EnvironmentModel."""
        self.model = EnvironmentModel(WORLD_W, WORLD_H, density=density, env_type="only_trees")
        # Limpa séries
        self.burned.clear()
        self.forested.clear()
        self.timesteps.clear()
        self.iteration = 0
        # Assegura que os parâmetros climáticos começam em valores seguros
        if self.model:
            self.model.humidity = 50  # evita divisão por zero
            self.model.rain_level = 0
            self.model.temperature = 25

    def step(self):
        """Executa um passo da simulação e actualiza métricas."""
        if not self.model:
            return
        self.model.step()
        burned = sum(1 for a in self.model.schedule if getattr(a, "state", None) == "burned")
        forested = sum(1 for a in self.model.schedule if getattr(a, "state", None) == "forested")
        self.burned.append(burned)
        self.forested.append(forested)
        self.timesteps.append(self.iteration)
        self.iteration += 1

    # ---------- Região GeoJSON ----------
    def set_geojson(self, geojson: dict):
        """Guarda o GeoJSON da região e computa bounds."""
        self.geojson = geojson
        lons, lats = [], []

        def _collect_coords(geom):
            gtype = geom.get("type")
            if gtype == "Polygon":
                return geom.get("coordinates", [[]])[0]
            if gtype == "MultiPolygon":
                coords = []
                for poly in geom.get("coordinates", []):
                    coords.extend(poly[0])
                return coords
            if gtype == "LineString":
                return geom.get("coordinates", [])
            if gtype == "MultiLineString":
                coords = []
                for line in geom.get("coordinates", []):
                    coords.extend(line)
                return coords
            return []

        self._shapes.clear()
        for feat in geojson.get("features", []):
            coords = _collect_coords(feat.get("geometry", {}))
            try:
                from shapely.geometry import shape as _shape
                self._shapes.append(_shape(feat.get("geometry", {})))
            except Exception:
                pass
            for lon, lat in coords:
                lons.append(lon)
                lats.append(lat)
        if lons and lats:
            self.bounds = (min(lons), max(lons), min(lats), max(lats))
        else:
            self.bounds = None

    # ---------- Helpers ----------
    def grid_to_latlon_color(self):
        if not self.bounds:
            return None, None, None
        min_lon, max_lon, min_lat, max_lat = self.bounds
        lon_span = max_lon - min_lon or 1e-9
        lat_span = max_lat - min_lat or 1e-9
        lons, lats, colors = [], [], []
        for agent in self.model.schedule:
            if hasattr(agent, "pos") and hasattr(agent, "pcolor") and getattr(agent, "state", None) != "forested":
                x, y = agent.pos
                lon = min_lon + (x / (WORLD_W - 1)) * lon_span
                lat = max_lat - (y / (WORLD_H - 1)) * lat_span
                # Verifica se ponto está dentro do polígono
                inside = True
                if self._shapes:
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

    def latlon_to_grid(self, lat: float, lon: float):
        if not self.bounds:
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
        if not self.model:
            return False
        grid = self.latlon_to_grid(lat, lon)
        if not grid:
            return False
        x, y = grid
        return self.model.start_fire_at(x, y)

    def grid_to_png_image(self):
        """Gera imagem PNG base64 da grelha inteira (sem precisar de polígono)."""
        from PIL import Image
        img = Image.new("RGBA", (WORLD_W, WORLD_H), (0, 0, 0, 255))
        for agent in self.model.schedule:
            if hasattr(agent, "pos") and hasattr(agent, "pcolor"):
                x, y = agent.pos
                color_hex = EncontrarCor(agent.pcolor)
                r = int(color_hex[1:3], 16)
                g = int(color_hex[3:5], 16)
                b = int(color_hex[5:7], 16)
                img.putpixel((x, y), (r, g, b, 255))
        # Define bounds fallback a PORTUGAL caso ainda não definidos
        bounds = self.bounds or PORTUGAL_BOUNDS
        upscale = 4
        img = img.resize((WORLD_W * upscale, WORLD_H * upscale), Image.NEAREST)
        import io, base64
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        return f"data:image/png;base64,{b64}", bounds


STATE = SimState()

# ----------------- FastAPI app -----------------
app = FastAPI(title="Wildfire Simulation API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------- Conexões WebSocket -----------------
class ConnectionManager:
    def __init__(self):
        self.active: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active:
            self.active.remove(websocket)

    async def broadcast(self, data: dict):
        """Envia JSON a todos os clientes conectados."""
        for ws in list(self.active):
            try:
                await ws.send_json(data)
            except Exception:
                # Cliente desconectou-se
                self.disconnect(ws)


manager = ConnectionManager()


# ----------------- Modelos Pydantic -----------------
class DensityReq(BaseModel):
    density: float = 0.5


class IgniteReq(BaseModel):
    lat: float
    lon: float


# ----------------- Endpoints REST -----------------
@app.post("/setup")
async def api_setup(req: DensityReq):
    STATE.setup_model(density=req.density)
    burned = 0
    forested = sum(1 for a in STATE.model.schedule if getattr(a, "state", None) == "forested") if STATE.model else 0
    air = STATE.model.air_agent if STATE.model else None
    pol = {"co": air.co_level if air else None,
           "co2": air.co2_level if air else None,
           "pm25": air.pm2_5_level if air else None,
           "pm10": air.pm10_level if air else None,
           "o2": air.o2_level if air else None}
    img_url, bounds = STATE.grid_to_png_image()
    return {"status": "ok", "bounds": bounds, "img": img_url, "burned": burned, "forested": forested, "pollutants": pol,
            "temperature": STATE.model.temperature if STATE.model else None,
            "humidity": STATE.model.humidity if STATE.model else None,
            "precipitation": STATE.model.rain_level if STATE.model else None,
            "ff_evo": {
                "tick": 0,
                "attack": 0,
                "firebreak": 0,
                "moving": 0,
                "idle": len([a for a in STATE.model.schedule if isinstance(a, FirefighterAgent)]) if STATE.model else 0,
                "water": len([a for a in STATE.model.schedule if isinstance(a, FirefighterAgent) and a.technique=='water']) if STATE.model else 0,
                "tech": len([a for a in STATE.model.schedule if isinstance(a, FirefighterAgent) and a.technique=='alternative']) if STATE.model else 0,
            }}


@app.post("/region")
async def api_region(geojson: dict):
    STATE.set_geojson(geojson)
    return {"bounds": STATE.bounds}


@app.post("/start")
async def api_start():
    if not STATE.model:
        raise HTTPException(400, "Model not configured – chame /setup primeiro.")
    STATE.running = True
    return {"running": True}


@app.post("/pause")
async def api_pause():
    STATE.running = False
    return {"running": False}


@app.post("/ignite")
async def api_ignite(req: IgniteReq):
    success = STATE.ignite_at(req.lat, req.lon)
    if success:
        STATE.running = True
    return {"success": success}


@app.post("/risk")
async def api_risk(geojson: dict):
    """Proxy para a API externa de cálculo de risco."""
    from main import BASE_URL, HEADERS  # reutiliza token existente
    import httpx

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{BASE_URL}/calculate-risk/", headers=HEADERS, json=geojson, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            raise HTTPException(502, f"Erro na API externa: {e}")


# ------------- Single Step Endpoint -------------
@app.post("/step")
async def api_step():
    if not STATE.model:
        raise HTTPException(400, "Model not configured – execute /setup first.")
    # Avança apenas um tick
    STATE.step()
    burned = STATE.burned[-1] if STATE.burned else 0
    forested = STATE.forested[-1] if STATE.forested else 0
    img_url, bounds = STATE.grid_to_png_image()
    return {
        "tick": STATE.iteration,
        "burned": burned,
        "forested": forested,
        "img": img_url,
        "bounds": bounds,
    }


# ----------------- WebSocket -----------------
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Mantém ligação viva; cliente pode enviar mensagens se desejar (comandos futuros).
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ----------------- Loop da simulação -----------------
async def sim_loop():
    """Loop assíncrono que avança a simulação e envia updates."""
    while True:
        if STATE.running and STATE.model:
            STATE.step()
            if STATE.iteration >= STATE.total_iters:
                STATE.running = False
                STATE.iteration = 0  # reset para nova execução
            burned = STATE.burned[-1] if STATE.burned else 0
            forested = STATE.forested[-1] if STATE.forested else 0
            img_url, bounds = STATE.grid_to_png_image()
            # --- Estatísticas adicionais ---
            temp = getattr(STATE.model, "temperature", None)
            wind_dir = getattr(STATE.model, "wind_direction", None)
            wind_speed = getattr(STATE.model, "wind_speed", None)
            humidity = getattr(STATE.model, "humidity", None)
            air = STATE.model.air_agent
            pollutants = {
                "co": air.co_level,
                "co2": air.co2_level,
                "pm25": air.pm2_5_level,
                "pm10": air.pm10_level,
                "o2": air.o2_level,
            }

            # Contagem de bombeiros por modo / técnica
            try:
                firefighters = [a for a in STATE.model.schedule if isinstance(a, FirefighterAgent)]
                ff_counts = {
                    "direct_attack": sum(1 for f in firefighters if f.mode == "direct_attack"),
                    "navigating": sum(1 for f in firefighters if f.mode == "navigating"),
                    "firebreak": sum(1 for f in firefighters if f.mode == "firebreak"),
                    "returning_home": sum(1 for f in firefighters if f.mode == "returning_home"),
                    "idle": sum(1 for f in firefighters if f.mode == "idle"),
                    "evacuated": sum(1 for f in firefighters if f.mode == "evacuated"),
                    "water": sum(1 for f in firefighters if getattr(f, "technique", "") == "water"),
                    "alternative": sum(1 for f in firefighters if getattr(f, "technique", "") == "alternative"),
                }
            except Exception:
                ff_counts = {}

            ff_evo = {
                "tick": STATE.iteration,
                "attack": ff_counts["direct_attack"],
                "firebreak": ff_counts["firebreak"],
                "moving": ff_counts["navigating"],
                "idle": ff_counts["idle"],
                "water": ff_counts["water"],
                "tech": ff_counts["alternative"],
            }

            await manager.broadcast({
                "tick": STATE.iteration,
                "burned": burned,
                "forested": forested,
                "img": img_url,
                "bounds": bounds,
                "stats": {
                    "temperature": temp,
                    "wind_direction": wind_dir,
                    "wind_speed": wind_speed,
                    "humidity": humidity,
                    "precipitation": getattr(STATE.model, "rain_level", None),
                    "pollutants": pollutants,
                    "firefighters": ff_counts,
                    "ff_evo": ff_evo,
                },
            })
        await asyncio.sleep(STEP_DELAY)


@app.on_event("startup")
async def startup_event():
    """Inicializa modelo e arranca loop background."""
    STATE.setup_model()
    asyncio.create_task(sim_loop())


# ----------------- Execução local -----------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend_api:app", host="0.0.0.0", port=8000, reload=True) 