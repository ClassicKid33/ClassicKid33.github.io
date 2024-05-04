import pandas as pd
import json
from datetime import datetime, timedelta
import numpy as np

# Get the current date
current_date = datetime.now().date()

# Determine the column name based on the current date
if current_date.day < 15:
    # If it's before the 15th of the current month, use the last day of two months ago
    column_date = (current_date.replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1)
else:
    # If it's on or after the 15th of the current month, use the last day of the previous month
    column_date = (current_date.replace(day=1) - timedelta(days=1))

# Format the column name as a string (YYYY-MM-DD)
column_name = column_date.strftime('%Y-%m-%d')

# Determine the column name for the previous year's corresponding month
prev_year_column_date = column_date.replace(year=column_date.year - 1)
prev_year_column_name = prev_year_column_date.strftime('%Y-%m-%d')

# Read the CSV file
df = pd.read_csv('home_prices.csv')

# Format the StateCodeFIPS column
df['StateCodeFIPS'] = df['StateCodeFIPS'].astype(str).str.zfill(2)

# Format the MunicipalCodeFIPS column
df['MunicipalCodeFIPS'] = df['MunicipalCodeFIPS'].astype(str).str.zfill(3)

# Create the GEO_ID column by merging StateCodeFIPS and MunicipalCodeFIPS
df['GEO_ID'] = df['StateCodeFIPS'] + df['MunicipalCodeFIPS']

# Convert the columns to numeric, replacing non-numeric values with NaN
df[column_name] = pd.to_numeric(df[column_name], errors='coerce')
df[prev_year_column_name] = pd.to_numeric(df[prev_year_column_name], errors='coerce')

# Calculate the home price growth rate YoY for each county
df['homegrowthYoY'] = ((df[column_name] - df[prev_year_column_name]) / df[prev_year_column_name]) * 100

# Read the GeoJSON file
with open('NewBasemapcopy.geojson') as file:
    geojson_data = json.load(file)

# Create a dictionary to store the home prices keyed by GEO_ID
home_prices = dict(zip(df['GEO_ID'], df[column_name]))

# Create a dictionary to store the home price growth rates keyed by GEO_ID, replacing NaN with None
home_growth_rates = {geo_id: None if np.isnan(growth_rate) else growth_rate for geo_id, growth_rate in zip(df['GEO_ID'], df['homegrowthYoY'])}

# Iterate over each feature in the GeoJSON data
for feature in geojson_data['features']:
    geo_id = feature['properties']['id']
    
    if geo_id in home_prices:
        # Update or add the home price value to the GeoJSON feature properties, formatted without decimals
        feature['properties']['HomePrices'] = int(home_prices[geo_id])
        
        if geo_id in home_growth_rates:
            # Update or add the home price growth rate to the GeoJSON feature properties, formatted with two decimal places
            feature['properties']['homegrowthYoY'] = round(home_growth_rates[geo_id], 2) if home_growth_rates[geo_id] is not None else None
        else:
            # Set the home price growth rate to null if there is no corresponding value
            feature['properties']['homegrowthYoY'] = None
    else:
        # Set the home price value and growth rate to null if there is no corresponding value
        feature['properties']['HomePrices'] = None
        feature['properties']['homegrowthYoY'] = None

# Overwrite the existing GeoJSON file with the updated data
with open('NewBasemapcopy.geojson', 'w') as file:
    json.dump(geojson_data, file, indent=2)
