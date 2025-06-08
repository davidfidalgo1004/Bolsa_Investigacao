import os
import requests

# 1. Token do Bearer (recomendado via variável de ambiente)
TOKEN = os.getenv("WILDFIRE_API_TOKEN", "david")
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

if __name__ == "__main__":
    # Exemplo GeoJSON
    geojson = {
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

    try:
        print("📍 Risco local:", calculate_risk(geojson, temperature=30, humidity=35))
        print("📅 Previsão (3 dias):", calculate_forecast(geojson, days=3))
        print("🇵🇹 Risco Portugal:", calculate_risk_portugal())
        print("📚 Todos os registos:", get_all_records())

        records = get_all_records()
        if records:
            # Supondo que o primeiro registo tem um campo 'id' em properties
            first_id = records[0]["properties"].get("id", 1)
            print("🧾 Registo #:", get_record(first_id))
            print("✍️ Atualizado:", update_record(first_id, is_wildfire=True))
            print("🗑️ Apagado:", delete_record(first_id))

        print("🔍 Pesquisa por nome:", search_records_by_name("Gaia"))

    except requests.HTTPError as err:
        print(f"⚠️ Erro HTTP {err.response.status_code}:", err.response.text)
