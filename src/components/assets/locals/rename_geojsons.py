import json
import statistics
import re
import time
from pathlib import Path
from typing import Optional

import requests

# --------------- Settings ---------------
USER_AGENT = "wildfire-sim-rename/1.0"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
SLEEP_BETWEEN_REQUESTS = 1.0  # segundos (para não sobrecarregar o serviço)

# --------------- Helpers ---------------

def slugify(text: str) -> str:
    """Transforma texto arbitrário num slug seguro para nome de ficheiro."""
    text = re.sub(r"[^A-Za-z0-9_\-]", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "area"


def region_name_from_geojson(geojson_obj: dict) -> Optional[str]:
    """Obtém nome de local usando Nominatim sobre o centroide do primeiro feature."""
    coords = []
    for feat in geojson_obj.get("features", []):
        geom = feat.get("geometry", {})
        gtype = geom.get("type")
        if gtype == "Polygon":
            coords.extend(geom.get("coordinates", [[]])[0])
            break
        elif gtype == "LineString":
            coords.extend(geom.get("coordinates", []))
            break
    if not coords:
        return None

    lons, lats = zip(*coords)
    lon = statistics.mean(lons)
    lat = statistics.mean(lats)

    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={"lat": lat, "lon": lon, "format": "json", "zoom": 10},
            headers={"User-Agent": USER_AGENT},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        display_name = data.get("display_name", "area").split(",")[0]
        return slugify(display_name)
    except Exception:
        return None


def rename_all_geojsons(dir_path: Path):
    """Percorre todos *.geojson no diretório e renomeia-os conforme região."""
    for f in dir_path.glob("*.geojson"):
        try:
            geojson_obj = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            print(f"⚠️ Não foi possível ler {f.name}. Saltando.")
            continue

        new_name_part = region_name_from_geojson(geojson_obj)
        if not new_name_part:
            print(f"ℹ️ {f.name}: nome de região não determinado.")
            continue

        new_file = f.with_name(f"{new_name_part}.geojson")
        if new_file.exists():
            # Se já existe, evita sobrepor; acrescenta sufixo
            idx = 1
            while new_file.exists():
                new_file = f.with_name(f"{new_name_part}_{idx}.geojson")
                idx += 1
        f.rename(new_file)
        print(f"✅ {f.name} → {new_file.name}")

        # Respeita limitação de uso da API
        time.sleep(SLEEP_BETWEEN_REQUESTS)


if __name__ == "__main__":
    current_dir = Path(__file__).parent
    rename_all_geojsons(current_dir) 