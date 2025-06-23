# Standard library imports
import os
import sys
from pathlib import Path

# Third-party imports
import requests
import argparse
import json

# Permite importar o gerador localizado no mesmo diretório
sys.path.append(str(Path(__file__).resolve().parent))

from geradorAPIs import generate_token

# 1. Token do Bearer (recomendado via variável de ambiente ou gerado automaticamente)
AUDIENCE = os.getenv("WILDFIRE_API_AUDIENCE", "ken01.utad.pt:8080")
TOKEN = os.getenv("WILDFIRE_API_TOKEN") or generate_token(AUDIENCE)

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}
BASE_URL = "http://ken01.utad.pt:8080"

# 2. Funções para cada endpoint

def calculate_risk(geojson, **params):
    """POST /calculate-risk/ — risco num polígono específico."""
    resp = requests.post(f"{BASE_URL}/calculate-risk/", headers=HEADERS, params=params, json=geojson)
    resp.raise_for_status()
    return resp.json()

def calculate_forecast(geojson, days):
    """POST /calculate-risk/forecast — previsão de risco para 1-7 dias."""
    resp = requests.post(f"{BASE_URL}/calculate-risk/forecast", headers=HEADERS,
                         params={"days": days}, json=geojson)
    resp.raise_for_status()
    return resp.json()

def calculate_risk_portugal():
    """GET /calculate-risk/portugal — risco médio para Portugal."""
    resp = requests.get(f"{BASE_URL}/calculate-risk/portugal", headers=HEADERS)
    resp.raise_for_status()
    return resp.json()

def get_all_records():
    """GET /records/ — lista todos os registos guardados."""
    resp = requests.get(f"{BASE_URL}/records/", headers=HEADERS)
    resp.raise_for_status()
    return resp.json()

def get_record(record_id):
    """GET /records/{record_id} — obtém um registo específico."""
    resp = requests.get(f"{BASE_URL}/records/{record_id}", headers=HEADERS)
    resp.raise_for_status()
    return resp.json()

def update_record(record_id, is_wildfire: bool):
    """PATCH /records/{record_id} — atualiza um registo existente."""
    resp = requests.patch(f"{BASE_URL}/records/{record_id}", headers=HEADERS,
                          json={"is_wildfire": is_wildfire})
    resp.raise_for_status()
    return resp.json()

def delete_record(record_id):
    """DELETE /records/{record_id} — apaga um registo."""
    resp = requests.delete(f"{BASE_URL}/records/{record_id}", headers=HEADERS)
    if resp.status_code == 204:
        return True
    resp.raise_for_status()
    return False

def search_records_by_name(name: str):
    """GET /records/search/by-location-name?name=... — pesquisa registos por nome."""
    resp = requests.get(f"{BASE_URL}/records/search/by-location-name", headers=HEADERS,
                        params={"name": name})
    resp.raise_for_status()
    return resp.json()

# 3. Exemplo de utilização

# ---------------- CLI ----------------

def _default_geojson():
    """GeoJSON pequeno para testes rápidos."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-8.8923, 39.9310], [-8.8897, 39.9296], [-8.8865, 39.9290],
                        [-8.8851, 39.9295], [-8.8847, 39.9360], [-8.8904, 39.9365],
                        [-8.8935, 39.9343], [-8.8951, 39.9325], [-8.8923, 39.9310],
                    ]]
                }
            }
        ]
    }

def main():
    parser = argparse.ArgumentParser(description="CLI para testar a Wildfire API")
    parser.add_argument("--geojson", help="Caminho para ficheiro GeoJSON a usar")
    parser.add_argument("--forecast", type=int, metavar="N", help="Dias de previsão (1-7)")
    parser.add_argument("--temperature", type=int, help="Temperatura a enviar, se aplicável")
    parser.add_argument("--humidity", type=int, help="Humidade a enviar, se aplicável")
    parser.add_argument("--risk-portugal", action="store_true", help="Calcular risco médio de Portugal")
    parser.add_argument("--list-records", action="store_true", help="Listar registos existentes")
    args = parser.parse_args()

    # Carregar GeoJSON
    if args.geojson:
        try:
            with open(args.geojson, "r", encoding="utf-8") as f:
                geojson = json.load(f)
        except Exception as e:
            print(f"⚠️ Não foi possível ler '{args.geojson}': {e}")
            return
    else:
        geojson = _default_geojson()

    try:
        # Operações principais
        if args.forecast:
            print("📅 Previsão (dias={}):".format(args.forecast),
                  calculate_forecast(geojson, days=args.forecast))
        else:
            extra = {}
            if args.temperature is not None:
                extra["temperature"] = args.temperature
            if args.humidity is not None:
                extra["humidity"] = args.humidity
            print("📍 Risco local:", calculate_risk(geojson, **extra))

        if args.risk_portugal:
            print("🇵🇹 Risco Portugal:", calculate_risk_portugal())

        if args.list_records:
            print("📚 Todos os registos:", get_all_records())

    except requests.HTTPError as err:
        print(f"⚠️ Erro HTTP {err.response.status_code}:", err.response.text)

if __name__ == "__main__":
    main()
