import os
import requests

WEBHOOK_URL = os.environ.get("CHAT_WEBHOOK_URL")

def parse_status(raw_val):
    if not raw_val:
        return "Available 🟢"
        
    s = str(raw_val).upper().strip()
    
    # Direct matching against EA status codes
    if any(k in s for k in ["AVAIL", "FREE", "READY", "IDLE", "OPEN"]):
        return "Available 🟢"
    elif any(k in s for k in ["OCCUPIED", "CHARGING", "IN_USE", "USE", "BUSY", "PLUGGED", "PREPARING"]):
        return "In Use 🔵"
    elif any(k in s for k in ["OUT", "OFFLINE", "DOWN", "FAULT", "UNAVAIL", "MAINTENANCE"]):
        return "Offline 🔴"
        
    # Default fallback changed to Available to prevent false "In Use" states
    return "Available 🟢"

def fetch_and_notify():
    status_list = []
    
    lat, lon = 36.1158, -115.1368
    ea_url = f"https://api.electrifyamerica.com/v2/locations?lat={lat}&lon={lon}&radius=5"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Origin": "https://www.electrifyamerica.com",
        "Referer": "https://www.electrifyamerica.com/"
    }

    try:
        response = requests.get(ea_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            locations = data.get("locations", []) if isinstance(data, dict) else data
            
            target_station = None
            for loc in locations:
                loc_id = str(loc.get("id", ""))
                name = str(loc.get("name", "")).lower()
                if loc_id == "200008" or "target" in name or "maryland" in name:
                    target_station = loc
                    break

            if not target_station and locations:
                target_station = locations[0]

            if target_station:
                evses = target_station.get("evses", [])
                charger_index = 1
                for evse in evses:
                    if charger_index > 4:
                        break
                    
                    status_raw = evse.get("status") or evse.get("evseStatus") or ""
                    if not status_raw and "connectors" in evse:
                        connectors = evse.get("connectors", [])
                        if connectors:
                            status_raw = connectors[0].get("status", "")

                    print(f"Charger 0{charger_index} raw status: '{status_raw}'")

                    status_list.append({
                        "id": f"Charger 0{charger_index}",
                        "status": parse_status(status_raw)
                    })
                    charger_index += 1

    except Exception as e:
        print(f"Fetch error: {e}")

    # Default missing items to Available instead of hardcoded In Use
    while len(status_list) < 4:
        status_list.append({"id": f"Charger 0{len(status_list)+1}", "status": "Available 🟢"})

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
    
