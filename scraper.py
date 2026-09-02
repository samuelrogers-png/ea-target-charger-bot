import os
import requests

WEBHOOK_URL = os.environ.get("CHAT_WEBHOOK_URL")
LOCATION_ID = 345793

def fetch_and_notify():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Authorization": "Basic d2ViOmd1ZXN0"
    }
    
    url = f"https://api.plugshare.com/v3/locations/345793"
    status_list = []
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            stations = data.get("stations", [])
            
            charger_index = 1
            for station in stations:
                outlets = station.get("outlets", [])
                for outlet in outlets:
                    if charger_index > 4:
                        break
                    
                    # Check operational status (1=Available, 2=In Use, 3=Offline)
                    # Fallback to checking boolean available/connector states if status is missing
                    raw_status = outlet.get("status")
                    
                    if raw_status == 1 or outlet.get("available") is True:
                        status_str = "Available 🟢"
                    elif raw_status == 2 or outlet.get("available") is False:
                        status_str = "In Use 🔵"
                    elif raw_status == 3:
                        status_str = "Offline 🔴"
                    else:
                        status_str = "Unknown ⚪"
                        
                    status_list.append({"id": f"Charger 0{charger_index}", "status": status_str})
                    charger_index += 1
        else:
            print(f"API Returned status code: {response.status_code}")
                
    except Exception as e:
        print(f"Error fetching data: {e}")

    # Fallback padding to ensure all 4 chargers display if array is empty
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
    
