import json

# Load the GeoJSON file
with open('NewBasemapcopy1.geojson') as file:
    geojson_data = json.load(file)

# Iterate over each feature in the GeoJSON
for feature in geojson_data['features']:
    properties = feature['properties']
    
    # Extract the necessary values from the properties
    county_name_base = properties.get('CountyNamesBase_NAMECOUNTY')
    lsad = properties.get('LSAD')
    
    if county_name_base is not None and lsad is not None:
        # Split the county name base into county name and state
        county_name, state = county_name_base.split(', ')
        
        # Create the new CountyName property
        county_name_new = f"{county_name} {lsad}, {state}"
        
        # Add the new CountyName property to the feature's properties
        properties['CountyName'] = county_name_new
    else:
        print(f"Skipping feature with missing properties: {properties}")

# Save the updated GeoJSON to a new file with pretty formatting
with open('NewBasemapcopy1.geojson', 'w') as file:
    json.dump(geojson_data, file, indent=2)
