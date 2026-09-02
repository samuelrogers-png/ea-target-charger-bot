import os
import requests

WEBHOOK_URL = os.environ.get("CHAT_WEBHOOK_URL")

# Electrify America Station ID for 4001 S Maryland Pkwy (Target Las Vegas)
EA_STATION_ID = "200008"

def fetch_and_notify():
    # Direct query to EA's live public telemetry endpoint
    url = f"https://api.electrifyamerica.com/v2/locations/{EA_STATION_ID}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }
    
    status_list = []
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            evses = data.get("evses", [])
            
            charger_index = 1
            for evse in evses:
                if charger_index > 4:
                    break
                
                # Live status string from EA API (AVAILABLE, IN_USE, OUT_OF_SERVICE)
                status_raw = str(evse.get("status", "")).upper()
                
                if "AVAIL" in status_raw:
                    status_str = "Available 🟢"
                elif "USE" in status_raw or "OCCUPIED" in status_raw:
                    status_str = "In Use 🔵"
                elif "OUT" in status_raw or "OFFLINE" in status_raw:
                    status_str = "Offline 🔴"
                else:
                    status_str = "In Use 🔵"  # Active charging fallback
                    
                status_list.append({"id": f"Charger 0{charger_index}", "status": status_str})
                charger_index += 1
        else:
            print(f"EA API status code: {response.status_code}")
            
    except Exception as e:
        print(f"Error fetching EA data: {e}")

    # Fallback padding to ensure all 4 chargers display
    while len(status_list) < 4:
        status_list.append({"id": f"Charger 0{len(status_list)+1}", "status": "Unknown ⚪"})

    # Google Chat Payload
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

    requests.post(WEBHOOK_URL, json=payload)

if __name__ == "__main__":
    fetch_and_notify()
    
