# Water Body Extraction

## Description
The `water-bodies-pipeline` project processes and analyzes data related to water bodies. It includes tools for validating city names, extracting water body information, and identifying water body names using Google Maps API.

## Features
- **City Validation**: Validate city names based on latitude and longitude using Google Geocoding API.
- **Water Body Extraction**: Extract large water bodies from shapefiles and associate them with nearby cities.
- **Water Body Name Identification**: Identify water body names near specific coordinates using Google Places API.

## Setup Instructions
1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/water-bodies-pipeline.git
   ```
2. Navigate to the project directory:
   ```bash
   cd water-bodies-pipeline
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables:
   - Add your Google API key to the scripts where required (e.g., `validate_city.py`, `extract_name_with_google_map.py`).

## Scripts Overview
### 1. `extract_water_bodies.py`
- **Must be run first.**
- Extracts large water bodies from shapefiles for specified states.
- Associates water bodies with nearby cities using OpenStreetMap's Nominatim API.
- Output: `large_waterbodies_4states.csv` and `large_waterbodies_4states.xlsx`

### 2. `validate_city.py`
- Validates city names in a CSV file using Google Geocoding API.
- Input: `data/before-modification.csv`
- Output: `data/after-google-city-validation.csv`

### 3. `extract_name_with_google_map.py`
- Identifies water body names near specific coordinates using Google Places API.
- Input: `correct.csv`
- Output: `correct.ndjson`

## Usage
1. Extract water bodies (must be done first):
   ```bash
   python extract_water_bodies.py
   ```
2. Run the city validation script:
   ```bash
   python validate_city.py
   ```
3. Identify water body names:
   ```bash
   python extract_name_with_google_map.py
   ```
