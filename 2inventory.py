import json
import csv
from datetime import datetime

# Load the GeoJSON file
with open('NewBasemapcopy1.geojson') as file:
    geojson_data = json.load(file)

# Get the current date
current_date = datetime.now()

# Determine the housing inventory column header based on the current date
if current_date.day <= 14:
    # If within the first two weeks of the month, use two months prior
    inventory_month = (current_date.month - 2) % 12
    if inventory_month == 0:
        inventory_month = 12
    inventory_year = current_date.year if inventory_month >= current_date.month else current_date.year - 1
else:
    # If after the first two weeks of the month, use the previous month
    inventory_month = (current_date.month - 1) % 12
    if inventory_month == 0:
        inventory_month = 12
    inventory_year = current_date.year if inventory_month >= current_date.month else current_date.year - 1

inventory_header = f"{datetime(inventory_year, inventory_month, 1).strftime('%B %Y')}"

# Load the housing inventory data from the CSV file
housing_data = {}
with open('inventory.csv', 'r', encoding='utf-16') as file:
    reader = csv.DictReader(file, delimiter='\t')
    for row in reader:
        county_name = row['Region']
        housing_inventory = row.get(inventory_header)
        if housing_inventory:
            housing_inventory = housing_inventory.replace(',', '')  # Remove comma from the value
            housing_data[county_name] = int(housing_inventory)
        else:
            housing_data[county_name] = None

# Iterate over each feature in the GeoJSON
for feature in geojson_data['features']:
    properties = feature['properties']
    county_name = properties.get('CountyName')
    
    if county_name in housing_data:
        # Add the housing inventory data to the feature's properties
        properties['HousingInventory'] = housing_data[county_name]
    else:
        # Set the housing inventory value as null if not found
        properties['HousingInventory'] = None

# Save the updated GeoJSON to a new file with pretty formatting
with open('NewBasemapcopy1.geojson', 'w') as file:
    json.dump(geojson_data, file, indent=2)
