import os
import requests

WEBHOOK_URL = os.environ.get("CHAT_WEBHOOK_URL")

# Cloudflare proxy relay endpoint
PROXY_URL = "https://summer-bush-6b1d.helpmeblizzard.workers.dev"

def parse_status(raw_val):
    if not raw_val:
        return "Unknown ⚪"
    
    s = str(raw_val).upper().strip()
    
    # Exact status mapping for Electrify America API values
    if any(k in s for k in ["OCCUPIED", "CHARGING", "IN_USE", "USE", "BUSY", "PLUGGED", "PREPARING"]):
        return "In Use 🔵"
    elif any(k in s for k in ["OUT", "OFFLINE", "DOWN", "FAULT", "UNAVAIL", "MAINTENANCE"]):
        return "Offline 🔴"
    elif any(k in s for k in ["AVAIL", "FREE", "READY", "IDLE", "OPEN"]):
        return "Available 🟢"
        
    return "Unknown ⚪"

def fetch_and_notify():
    status_list = []
    
    try:
        # Route through Cloudflare proxy relay
        response = requests.get(PROXY_URL, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract EVSE objects from API payload
            evses = []
            if isinstance(data, dict):
                evses = data.get("evses") or data.get("data", {}).get("evses") or []
            elif isinstance(data, list):
                evses = data

            charger_index = 1
            for evse in evses:
                if charger_index > 4:
                    break
                
                # Check top-level EVSE status or nested connectors status
                status_raw = evse.get("status") or evse.get("evseStatus") or ""
                if not status_raw and "connectors" in evse:
                    connectors = evse.get("connectors", [])
                    if connectors:
                        status_raw = connectors[0].get("status", "")

                status_list.append({
                    "id": f"Charger 0{charger_index}",
                    "status": parse_status(status_raw)
                })
                charger_index += 1

    except Exception as e:
        print(f"Relay fetch error: {e}")

    # Fallback padding if fewer than 4 items are parsed
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
    
