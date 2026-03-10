import requests
import csv
import time
from datetime import datetime

# =====================================
# CONFIGURATION
# =====================================

# QuestDB config
QUESTDB_URL = "http://budzow.hack:9000/exec"
QUESTDB_USER = "admin"
QUESTDB_PASS = "B4Ve2PdM!Zwd"

# ESA API config
ESA_API_URL = "https://esa.nask.pl/api/data/id/1381"
ESA_BEARER_TOKEN = "eyJhbGciOiJIUzUxMiJ9.eyJqdGkiOiJmMWJkMDljYS0zZGJhLTRiOGYtYjZlNS0zM2M3ZTU0MDAzNjUiLCJpc3MiOiJFU0EiLCJzdWIiOiJlc2EubmFzay5wbCIsImlhdCI6MTc3MjYzOTgzOSwiZXhwIjoxNzcyODEyNjM5LCJBdXRob3JpdGllcyI6WyJTTU9HX1BBR0UiXX0.S1gsHJDY7Rj93jlCLj6ltqOW91lAqOfumTx386XpbwHuX8BIIC6oRmTSNVvbmjJsmpNa1h39X4RqdbwcDHUtpQ"

OUTPUT_FILE = "sensor_data.csv"
INTERVAL_SECONDS = 30

# QuestDB query
QUERY = """
SELECT id, temperature, humidity, timestamp, pm25, pm10
FROM sensors
LATEST ON timestamp PARTITION BY id
"""

# =====================================
# QUESTDB FETCH
# =====================================

def fetch_questdb():
    try:
        response = requests.get(
            QUESTDB_URL,
            params={"query": QUERY},
            auth=(QUESTDB_USER, QUESTDB_PASS),
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        dataset = data.get("dataset", [])

        results = []
        for row in dataset:
            results.append([
                "questdb",              # source
                row[0],                 # id
                row[1],                 # temperature
                row[2],                 # humidity
                row[3],                 # timestamp
                row[4],                 # pm25
                row[5]                  # pm10
            ])
        return results

    except Exception as e:
        print(f"[{datetime.now()}] QuestDB error:", e)
        return []

# =====================================
# ESA API FETCH
# =====================================

def fetch_esa_api():
    try:
        headers = {
            "Authorization": f"Bearer {ESA_BEARER_TOKEN}"
        }

        response = requests.get(
            ESA_API_URL,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()

        data = response.json()
        sensors = data.get("sensors", [])

        results = []
        for sensor in sensors:
            last = sensor.get("lastMeasurement", {})
            pm25 = last.get("pm25", {}).get("value")
            pm10 = last.get("pm10", {}).get("value")
            humidity = last.get("humidity")
            temperature = last.get("temperature")

            results.append([
                "esa_api",             # source
                sensor.get("name"),    # id (using name instead)
                temperature,
                humidity,
                datetime.now().isoformat(),
                pm25,
                pm10
            ])

        return results

    except Exception as e:
        print(f"[{datetime.now()}] ESA API error:", e)
        return []

# =====================================
# SAVE TO CSV
# =====================================

def save_to_csv(rows):
    if not rows:
        return

    file_exists = False
    try:
        with open(OUTPUT_FILE, "r"):
            file_exists = True
    except FileNotFoundError:
        file_exists = False

    with open(OUTPUT_FILE, "a", newline="") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow([
                "source",
                "sensor_id",
                "temperature",
                "humidity",
                "timestamp",
                "pm25",
                "pm10"
            ])

        writer.writerows(rows)

# =====================================
# MAIN LOOP
# =====================================

def main():
    print("Starting combined data logger...")

    while True:
        print(f"[{datetime.now()}] Fetching data...")

        quest_data = fetch_questdb()
        esa_data = fetch_esa_api()

        all_data = quest_data + esa_data

        if all_data:
            save_to_csv(all_data)
            print(f"[{datetime.now()}] Saved {len(all_data)} records.")
        else:
            print(f"[{datetime.now()}] No data received.")

        time.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    main()