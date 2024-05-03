import pandas as pd
import json

# Read the CSV file
df = pd.read_csv('home_prices.csv')

# Format the StateCodeFIPS column
df['StateCodeFIPS'] = df['StateCodeFIPS'].astype(str).str.zfill(2)

# Format the MunicipalCodeFIPS column
df['MunicipalCodeFIPS'] = df['MunicipalCodeFIPS'].astype(str).str.zfill(3)

# Create the GEO_ID column by merging StateCodeFIPS and MunicipalCodeFIPS
df['GEO_ID'] = df['StateCodeFIPS'] + df['MunicipalCodeFIPS']

# Convert the '2024-03-31' column to integer to remove decimal points
df['2024-03-31'] = df['2024-03-31'].astype(int)

# Read the GeoJSON file
with open('NewBasemapcopy.geojson') as file:
    geojson_data = json.load(file)

# Create a dictionary to store the home prices keyed by GEO_ID
home_prices = dict(zip(df['GEO_ID'], df['2024-03-31']))

# Iterate over each feature in the GeoJSON data
for feature in geojson_data['features']:
    geo_id = feature['properties']['id']
    
    if geo_id in home_prices:
        # Add the home price value to the GeoJSON feature properties with the name "HomePrices"
        feature['properties']['HomePrices'] = home_prices[geo_id]
    else:
        # Set the home price value to null for GEO_IDs not found in the CSV
        feature['properties']['HomePrices'] = None

# Overwrite the existing GeoJSON file with the updated data
with open('NewBasemapcopy.geojson', 'w') as file:
    json.dump(geojson_data, file, indent=2)
