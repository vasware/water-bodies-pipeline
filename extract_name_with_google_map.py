#!/usr/bin/env python3

import pandas as pd
import requests
import time
import json
from math import radians, sin, cos, atan2, sqrt
from tqdm import tqdm

API_KEY = "YOUR_GOOGLE_API_KEY"

WATER_KEYWORDS = [
    "lake", "river", "pond", "reservoir", "creek", "stream",
    "bay", "canal", "waterfall", "falls", "marsh", "wetland",
    "lagoon", "harbor", "harbour"
]

PLACES_NEARBY = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
GEOCODE = "https://maps.googleapis.com/maps/api/geocode/json"


def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))


def safe_request(url, params, retries=3, delay=5):
    """Safe requests with retry/backoff to avoid SSL crashes."""
    for i in range(retries):
        try:
            return requests.get(url, params=params, timeout=20).json()
        except requests.exceptions.SSLError:
            if i < retries - 1:
                time.sleep(delay * (i + 1))
            else:
                return {"status": "ERROR", "results": []}
        except requests.exceptions.RequestException:
            if i < retries - 1:
                time.sleep(delay * (i + 1))
            else:
                return {"status": "ERROR", "results": []}


def fetch_places(url, params, max_pages=2):
    results = {}
    for _ in range(max_pages):
        r = safe_request(url, params)
        if r.get("status") != "OK":
            break
        for place in r.get("results", []):
            pid = place.get("place_id")
            loc = place.get("geometry", {}).get("location", {})
            if pid and loc:
                results[pid] = {
                    "place_id": pid,
                    "name": place.get("name", ""),
                    "lat": loc["lat"],
                    "lon": loc["lng"],
                    "types": place.get("types", []),
                }
        token = r.get("next_page_token")
        if not token:
            break
        time.sleep(2)
        params = {"key": API_KEY, "pagetoken": token}
    return results


def reverse_geocode(lat, lon):
    r = safe_request(GEOCODE, {"latlng": f"{lat},{lon}", "key": API_KEY})
    for res in r.get("results", []):
        name = res.get("formatted_address", "")
        if any(k in name.lower() for k in WATER_KEYWORDS):
            return name
    return None


def get_water_names(lat, lon, radius=100):
    results = {}
    for kw in WATER_KEYWORDS:
        params = {"key": API_KEY, "location": f"{lat},{lon}", "radius": radius, "keyword": kw}
        results.update(fetch_places(PLACES_NEARBY, params))

    filtered = []
    for r in results.values():
        d = haversine_m(lat, lon, r["lat"], r["lon"])
        r["distance_m"] = d
        filtered.append(r)
            
    return sorted(filtered, key=lambda r: (r["distance_m"], r["name"]))


def main():
    df = pd.read_csv("correct.csv")

    # Append mode → don’t overwrite existing
    with open("correct.ndjson", "a", encoding="utf-8") as f:
        for idx, row in tqdm(df.iterrows(), total=len(df), desc="Processing"):

            lat, lon = row["Lat"], row["Lon"]
            water_places = get_water_names(lat, lon)

            record = {
                "row_number": int(idx),
                "original_google_name": row.get("google_name", ""),
                "matches": [
                    {
                        "name": wp["name"],
                        "distance_m": wp["distance_m"],
                        "types": wp.get("types", []),
                        "lat": wp["lat"],
                        "lon": wp["lon"]
                    }
                    for wp in water_places
                ]
            }

            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            f.flush()  # flush after every row


if __name__ == "__main__":
    main()
