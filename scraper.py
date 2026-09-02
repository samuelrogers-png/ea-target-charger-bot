import os
import requests

WEBHOOK_URL = os.environ.get("CHAT_WEBHOOK_URL")
NREL_API_KEY = os.environ.get("NREL_API_KEY", "DEMO_KEY")

# Target Coordinates for 4001 S Maryland Pkwy (Target Las Vegas)
LAT = "36.1070"
LON = "-115.1364"

def fetch_and_notify():
    # NLR API query using direct coordinates and fuel_type=ELEC
    url = f"https://developer.nlr.gov/api/alt-fuel-stations/v1/nearest.json?api_key={NREL_API_KEY}&latitude={LAT}&longitude={LON}&fuel_type=ELEC&limit=5"
    
    status_list = []
    
    try:
        response = requests.get(url, timeout=10)
        print(f"API HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            stations = data.get("fuel_stations", [])
            
            # Find the Electrify America station at Maryland Pkwy
            ea_station = None
            for station in stations:
                network = str(station.get("ev_network", "")).upper()
                address = str(station.get("street_address", "")).upper()
                if "ELECTRIFY" in network or "MARYLAND" in address:
                    ea_station = station
                    break
            
            # Default to closest station if specific match loop passes
            if not ea_station and stations:
                ea_station = stations[0]

            if ea_station:
                status_code = ea_station.get("status_code", "E")
                
                if status_code == "E":
                    general_status = "Available 🟢"
                elif status_code == "T":
                    general_status = "Offline 🔴"
                else:
                    general_status = "In Use 🔵"
                
                for i in range(1, 5):
                    status_list.append({"id": f"Charger 0{i}", "status": general_status})
            else:
                print("No matching EV station found in payload.")
        else:
            print(f"API Error Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"Script execution error: {e}")

    # Fallback padding to ensure card renders
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
    else:
        print("Missing CHAT_WEBHOOK_URL secret.")

if __name__ == "__main__":
    fetch_and_notify()
    
