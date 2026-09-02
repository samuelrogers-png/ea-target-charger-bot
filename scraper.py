import os
import requests

WEBHOOK_URL = os.environ.get("CHAT_WEBHOOK_URL")

# Hardcoded fallback URL so you don't need GitHub Secrets
PROXY_URL = os.environ.get("PROXY_URL", "https://summer-bush-6b1d.helpmeblizzard.workers.dev")

def fetch_and_notify():
    status_list = []
    
    try:
        response = requests.get(PROXY_URL, timeout=15)
        print(f"Proxy HTTP status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            evses = data.get("evses", [])
            
            charger_index = 1
            for evse in evses:
                if charger_index > 4:
                    break
                
                status_raw = str(evse.get("status", "")).upper()
                
                if "AVAIL" in status_raw:
                    status_str = "Available 🟢"
                elif "USE" in status_raw or "OCCUPIED" in status_raw or "CHARGING" in status_raw:
                    status_str = "In Use 🔵"
                elif "OUT" in status_raw or "OFFLINE" in status_raw:
                    status_str = "Offline 🔴"
                else:
                    status_str = "In Use 🔵"
                    
                status_list.append({"id": f"Charger 0{charger_index}", "status": status_str})
                charger_index += 1
        else:
            print(f"Proxy Error: {response.text[:200]}")
            
    except Exception as e:
        print(f"Error calling proxy relay: {e}")

    while len(status_list) < 4:
        status_list.append({"id": f"Charger 0{len(status_list)+1}", "status": "Unknown ⚪"})

    payload = {
        "cardsV2": [{
            "cardId": "ea_target_auto_update",
            "card": {
                "header": {
                    "title": "⚡ EA Charger Status (Live)",
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
    
