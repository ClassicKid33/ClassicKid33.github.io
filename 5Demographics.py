import pandas as pd
import json

def add_demographics_to_geojson(
    excel_path: str,
    geojson_path: str
):
    """
    Reads Excel data (total population in col C and white population in col G)
    and updates the GeoJSON with a 'demographics' property under each feature.
    The link between Excel and GeoJSON is the 'GEO_ID' field.
    """
    
    # 1. Read the Excel file, skipping the first 2 rows to start at row 3
    df = pd.read_excel(
        excel_path, 
        header=2  # Row 3 in Excel => row 0 in the DataFrame
    )
    
    # Rename columns for clarity. Adjust these as needed for your actual column names.
    #    Col A -> GEO_ID  (df.columns[0])
    #    Col C -> total_population (df.columns[2])
    #    Col G -> white_population (df.columns[6])
    df.rename(
        columns={
            df.columns[0]: "GEO_ID",
            df.columns[2]: "total_population",
            df.columns[6]: "white_population"
        }, 
        inplace=True
    )
    
    # 2. Create a dictionary keyed by GEO_ID for quick lookups
    df_for_lookup = df[["GEO_ID", "total_population", "white_population"]].copy()
    df_for_lookup.set_index("GEO_ID", inplace=True)
    
    demographics_dict = df_for_lookup.to_dict(orient="index")
    
    # 3. Load the existing GeoJSON file
    with open(geojson_path, "r", encoding="utf-8") as f:
        geojson_data = json.load(f)
    
    # 4. Iterate over each feature in the GeoJSON and match to the Excel data
    for feature in geojson_data.get("features", []):
        # Extract the GEO_ID from the feature's properties
        feature_geo_id = feature["properties"].get("GEO_ID")
        
        if feature_geo_id in demographics_dict:
            total_pop = demographics_dict[feature_geo_id]["total_population"]
            white_pop = demographics_dict[feature_geo_id]["white_population"]
            
            # Prevent division by zero if total_pop is None or 0
            if total_pop and white_pop and total_pop != 0:
                white_percentage = (white_pop / total_pop) * 100
            else:
                white_percentage = None
            
            # Add the 'demographics' property
            feature["properties"]["demographics"] = {
                "total_population": total_pop,
                "white_population": white_pop,
                "white_percentage": white_percentage
            }
        else:
            # If no match, optionally leave an empty dict or skip
            feature["properties"]["demographics"] = {}
    
    # 5. Write out the updated GeoJSON (overwrites the same file)
    with open(geojson_path, "w", encoding="utf-8") as f:
        json.dump(geojson_data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    excel_file = "Demographics.xls"
    geojson_file = "NewBasemapcopy.geojson"
    
    add_demographics_to_geojson(excel_file, geojson_file)
    print("Demographics added to GeoJSON successfully!")
