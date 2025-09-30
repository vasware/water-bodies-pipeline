import pandas as pd
import requests
import time
import sys

# -------------------------------
# Config
# -------------------------------
API_KEY = "YOUR_GOOGLE_API"
input_csv = "data/before-modification.csv"  # Updated to a local path
output_csv = "data/after-google-city-validation.csv"  # Updated to a local path
pause_every = 10     # pause every N requests to respect rate limits
pause_seconds = 0.1  # pause duration

# -------------------------------
# Step 1: Load CSV
# -------------------------------
df = pd.read_csv(input_csv)
n_points = len(df)

# -------------------------------
# Step 2: Function to get city from Google
# -------------------------------
def get_city_from_google(lat, lon):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "latlng": f"{lat},{lon}",
        "key": API_KEY
    }
    
    try:
        resp = requests.get(url, params=params).json()
        if resp['status'] != 'OK' or not resp.get('results'):
            return None
        
        result = resp['results'][0]
        city = None
        
        # Priority: locality > postal_town > administrative_area_level_3 > sublocality > county
        for comp in result['address_components']:
            types = comp['types']
            if "locality" in types or "postal_town" in types:
                city = comp['long_name']
                break
        if not city:
            for comp in result['address_components']:
                types = comp['types']
                if "administrative_area_level_3" in types or "sublocality" in types:
                    city = comp['long_name']
                    break
        if not city:
            for comp in result['address_components']:
                if "administrative_area_level_2" in comp['types']:
                    city = comp['long_name']
                    break
        return city
    except Exception as e:
        print("Error:", e)
        return None


# -------------------------------
# Step 3: Validate each row
# -------------------------------
validated_cities = []
city_valid_flags = []

for i, row in df.iterrows():
    lat, lon, csv_city = row['Lat'], row['Lon'], row['City']
    city_name = get_city_from_google(lat, lon)
    
    validated_cities.append(city_name if city_name else "Unknown")
    city_valid_flags.append(city_name.lower() == csv_city.lower() if city_name else False)
    
    # Progress tracking
    percent = (i + 1) / n_points * 100
    sys.stdout.write(f"\rProcessing: {i+1}/{n_points} ({percent:.1f}%)")
    sys.stdout.flush()
    
    # Respect API rate limits
    if (i + 1) % pause_every == 0:
        time.sleep(pause_seconds)

print("\n✅ Finished city validation.")

# -------------------------------
# Step 4: Save results
# -------------------------------
df['validated_city'] = validated_cities
df['city_valid'] = city_valid_flags
df.to_csv(output_csv, index=False)
print(f"✅ Results saved to {output_csv}")
