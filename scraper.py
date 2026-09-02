import os
import requests

WEBHOOK_URL = os.environ.get("CHAT_WEBHOOK_URL")
NREL_API_KEY = os.environ.get("NREL_API_KEY", "DEMO_KEY")

# Target Station - 4001 S Maryland Pkwy, Las Vegas, NV
STATION_ADDRESS = "4001 S Maryland Pkwy"
STATION_ZIP = "89119"

def fetch_and_notify():
    url = f"https://developer.nlr.gov/api/alt-fuel-stations/v1/nearest.json?api_key={NREL_API_KEY}&location={STATION_ADDRESS}+{STATION_ZIP}&ev_network=Electrify+America&limit=1"
    
    status_list = []
    
    try:
        response = requests.get(url, timeout=10)
        print(f"API status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            stations = data.get("fuel_stations", [])
            
            if stations:
                station = stations[0]
                status_code = station.get("status_code")
                
                if status_code == "E":
                    general_status = "Available 🟢"
                elif status_code == "T":
                    general_status = "Offline 🔴"
                else:
                    general_status = "In Use 🔵"
                
                for i in range(1, 5):
                    status_list.append({"id": f"Charger 0{i}", "status": general_status})
            else:
                print("No station found matching location criteria.")
        else:
            print(f"API Error payload: {response.text[:200]}")
            
    except Exception as e:
        print(f"Error fetching data: {e}")

    # Fallback padding
    while len(status_list) < 4:
        status_list.append({"id": f"Charger 0{len(status_list)+1}", "status": "Unknown ⚪"})

    payload = {
        "cardsV2": [{
            "cardId": "ea_target_auto_update",
            "card": {
                "header": {
                    "title": "⚡ EA Charger Status (Automated)",
                    "subtitle": "Target (4001 S Maryland Pkwy)"
                },
                "sections": [{
                    "widgets": [
                        {"decoratedText": {"topLabel": item["id"], "text": item["status"]}}
                        for item in status_list
                    ]
                }]
            }
        }]
    }

    if WEBHOOK_URL:
        requests.post(WEBHOOK_URL, json=payload)

if __name__ == "__main__":
    fetch_and_notify()
    
