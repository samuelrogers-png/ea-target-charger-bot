import os
import requests

WEBHOOK_URL = os.environ.get("CHAT_WEBHOOK_URL")
# Target at 4001 S Maryland Pkwy PlugShare ID:
LOCATION_ID = 345793

def fetch_and_notify():
    # Public web client authorization header required by PlugShare's endpoints
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Authorization": "Basic d2ViOmd1ZXN0"  # PlugShare web client auth key
    }
    
    url = f"https://api.plugshare.com/v3/locations/345793"
    status_list = []
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        # If the API endpoint succeeds
        if response.status_code == 200:
            data = response.json()
            stations = data.get("stations", [])
            
            charger_index = 1
            for station in stations:
                for outlet in station.get("outlets", []):
                    if charger_index > 4:
                        break
                    
                    # Status mappings: 1=Available, 2=In Use/Occupied, 3=Offline
                    outlet_status = outlet.get("status", 0)
                    if outlet_status == 1:
                        status_str = "Available 🟢"
                    elif outlet_status == 2:
                        status_str = "In Use 🔵"
                    elif outlet_status == 3:
                        status_str = "Offline 🔴"
                    else:
                        status_str = "Unknown ⚪"
                        
                    status_list.append({"id": f"Charger 0{charger_index}", "status": status_str})
                    charger_index += 1
        else:
            print(f"API Returned status code: {response.status_code}")
                
    except Exception as e:
        print(f"Error fetching data: {e}")

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
