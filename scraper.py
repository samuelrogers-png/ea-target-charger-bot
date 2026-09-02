import os
import requests
import cloudscraper

WEBHOOK_URL = os.environ.get("CHAT_WEBHOOK_URL")
EA_STATION_ID = "200008"

def fetch_and_notify():
    # Use cloudscraper to simulate a real browser TLS handshake
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    
    url = f"https://api.electrifyamerica.com/v2/locations/{EA_STATION_ID}"
    status_list = []
    
    try:
        response = scraper.get(url, timeout=15)
        print(f"EA API status code: {response.status_code}")
        
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
                elif "USE" in status_raw or "OCCUPIED" in status_raw:
                    status_str = "In Use 🔵"
                elif "OUT" in status_raw or "OFFLINE" in status_raw:
                    status_str = "Offline 🔴"
                else:
                    status_str = "In Use 🔵"
                    
                status_list.append({"id": f"Charger 0{charger_index}", "status": status_str})
                charger_index += 1
        else:
            print(f"API Error payload: {response.text[:200]}")
            
    except Exception as e:
        print(f"Error fetching EA data: {e}")

    # Fallback padding to guarantee 4 rows
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

    if WEBHOOK_URL:
        requests.post(WEBHOOK_URL, json=payload)
    else:
        print("Error: CHAT_WEBHOOK_URL environment variable is missing.")

if __name__ == "__main__":
    fetch_and_notify()
    
