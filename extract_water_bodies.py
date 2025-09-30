# -----------------------------
# Imports
# -----------------------------
import os
import geopandas as gpd
import pandas as pd
from pathlib import Path
from zipfile import ZipFile
import requests
import time
import sys

# -----------------------------
# Config
# -----------------------------
states = {
    "NY": "https://prd-tnm.s3.amazonaws.com/StagedProducts/Hydrography/NHD/State/Shape/NHD_H_New_York_State_Shape.zip",
    "NJ": "https://prd-tnm.s3.amazonaws.com/StagedProducts/Hydrography/NHD/State/Shape/NHD_H_New_Jersey_State_Shape.zip",
    "PA": "https://prd-tnm.s3.amazonaws.com/StagedProducts/Hydrography/NHD/State/Shape/NHD_H_Pennsylvania_State_Shape.zip",
    "CT": "https://prd-tnm.s3.amazonaws.com/StagedProducts/Hydrography/NHD/State/Shape/NHD_H_Connecticut_State_Shape.zip"
}

min_acres = 50
acre_to_m2 = 4046.8564224
base_folder = Path("")
base_folder.mkdir(exist_ok=True)

all_rows = []

# -----------------------------
# Mode switch
# -----------------------------
TEST_MODE = True    # ✅ set to False for full run
TEST_LIMIT = 10     # how many to process per state in test mode

# -----------------------------
# Helper: get city from lat/lon
# -----------------------------
def get_city(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&zoom=10&addressdetails=1"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200:
            data = r.json()
            return (
                data.get("address", {}).get("town")
                or data.get("address", {}).get("city")
                or data.get("address", {}).get("village")
                or data.get("address", {}).get("hamlet")
            )
    except:
        return None
    return None

# -----------------------------
# Process each state
# -----------------------------
for state, url in states.items():
    print(f"\nProcessing {state}...")
    zip_path = base_folder / f"NHD_{state}.zip"
    shp_folder = base_folder
    
    # Download shapefile
    if not zip_path.exists():
        os.system(f'wget "{url}" -O {zip_path}')
    
    # Unzip
    with ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(shp_folder)
    
    # Find NHDWaterbody.shp
    real_shp_folder = shp_folder / "Shape"
    shp_file = list(real_shp_folder.glob("*NHDWaterbody.shp"))[0]
    
    # Load shapefile
    gdf = gpd.read_file(shp_file)
    
    # Compute area
    gdf = gdf.to_crs("EPSG:5070")  # Equal-area CRS
    gdf["area_m2"] = gdf.geometry.area
    gdf = gdf[gdf["area_m2"] >= min_acres * acre_to_m2]
    
    # Compute centroids
    gdf = gdf.to_crs("EPSG:4326")
    gdf["centroid_lat"] = gdf.geometry.centroid.y
    gdf["centroid_lon"] = gdf.geometry.centroid.x
    gdf["area_acres"] = gdf["area_m2"] / acre_to_m2
    
    total = len(gdf)
    print(f"  Found {total} large waterbodies in {state}")
    
    # --- Limit for test mode ---
    if TEST_MODE:
        gdf = gdf.head(TEST_LIMIT)
        total = len(gdf)
        print(f"  ⚡ Test mode active: processing only {total}")
    
    # Iterate with progress
    for i, (idx, r) in enumerate(gdf.iterrows(), start=1):
        coord_id = f"{r['centroid_lat']:.6f},{r['centroid_lon']:.6f}"
        
        # Lookup city
        city = get_city(r["centroid_lat"], r["centroid_lon"])
        
        # Only sleep in full mode (to respect Nominatim’s 1 request/sec policy)
        if not TEST_MODE:
            time.sleep(1)
        
        # Waterbody name (if available)
        water_name = r.get("GNIS_NAME", None)
        
        all_rows.append({
            "body_id": coord_id,
            "waterbody_name": water_name,
            "city": city,
            "state": state,
            "approx_area_acres": round(r["area_acres"], 2),
            "centroid_lat": round(r["centroid_lat"], 6),
            "centroid_lon": round(r["centroid_lon"], 6)
        })
        
        # Progress percentage
        percent = (i / total) * 100
        sys.stdout.write(f"\r  Progress {i}/{total} ({percent:.1f}%)")
        sys.stdout.flush()
    
    print("\n  Done.")

# -----------------------------
# Save combined CSV/XLSX
# -----------------------------
df = pd.DataFrame(all_rows)
df.to_csv("large_waterbodies_4states.csv", index=False)
df.to_excel("large_waterbodies_4states.xlsx", index=False)

print(f"\n✅ Saved {len(df)} waterbodies for 4 states to CSV/XLSX with names and cities.")
