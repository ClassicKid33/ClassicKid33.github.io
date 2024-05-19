import os
import time
import pandas as pd
import json
from datetime import datetime, timedelta
import numpy as np
import logging
import requests

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

try:
    # Set up the download directory
    download_dir = os.path.join(os.path.expanduser("~"), "Desktop", "leaflet")
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    
    # URL of the CSV file
    csv_url = "https://files.zillowstatic.com/research/public_csvs/zori/County_zori_uc_sfrcondomfr_sm_month.csv?t=1716078501"
    
    # Path to save the downloaded file
    download_file_path = os.path.join(download_dir, "County_zori_uc_sfrcondomfr_sm_month.csv")
    
    # Download the file
    logging.info("Downloading the CSV file from the direct link.")
    response = requests.get(csv_url)
    with open(download_file_path, 'wb') as file:
        file.write(response.content)
    
    # Check if the file was downloaded successfully
    if os.path.exists(download_file_path) and os.path.getsize(download_file_path) > 0:
        logging.info("Renaming the downloaded file to rent_prices.csv.")
        # Rename the downloaded file to rent_prices.csv
        new_file = os.path.join(download_dir, "rent_prices.csv")
        if os.path.exists(new_file):
            os.remove(new_file)  # Remove the existing file if it exists
        os.rename(download_file_path, new_file)
    else:
        logging.error("Downloaded file not found.")
        exit(1)

    # Proceed with the existing data processing code
    try:
        logging.info("Processing the downloaded data.")
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

        # Determine the column name for the previous month
        prev_month_column_date = column_date.replace(day=1) - timedelta(days=1)
        prev_month_column_name = prev_month_column_date.strftime('%Y-%m-%d')

        # Read the CSV file
        df = pd.read_csv(new_file)

        # Format the StateCodeFIPS column
        df['StateCodeFIPS'] = df['StateCodeFIPS'].astype(str).str.zfill(2)

        # Format the MunicipalCodeFIPS column
        df['MunicipalCodeFIPS'] = df['MunicipalCodeFIPS'].astype(str).str.zfill(3)

        # Create the GEO_ID column by merging StateCodeFIPS and MunicipalCodeFIPS
        df['GEO_ID'] = df['StateCodeFIPS'] + df['MunicipalCodeFIPS']

        # Convert the columns to numeric, replacing non-numeric values with NaN
        df[column_name] = pd.to_numeric(df[column_name], errors='coerce')
        df[prev_year_column_name] = pd.to_numeric(df[prev_year_column_name], errors='coerce')
        df[prev_month_column_name] = pd.to_numeric(df[prev_month_column_name], errors='coerce')

        # Calculate the rent price growth rate YoY for each county
        df['rentgrowthYoY'] = ((df[column_name] - df[prev_year_column_name]) / df[prev_year_column_name]) * 100

        # Calculate the rent price growth rate MoM for each county
        df['rentgrowthMoM'] = ((df[column_name] - df[prev_month_column_name]) / df[prev_month_column_name]) * 100

        # Read the GeoJSON file
        with open('NewBasemapcopy1.geojson') as file:
            geojson_data = json.load(file)

        # Create a dictionary to store the rent prices keyed by GEO_ID
        rent_prices = dict(zip(df['GEO_ID'], df[column_name]))

        # Create a dictionary to store the rent price growth rates YoY keyed by GEO_ID, replacing NaN with None
        rent_growth_rates_yoy = {geo_id: None if np.isnan(growth_rate) else growth_rate for geo_id, growth_rate in zip(df['GEO_ID'], df['rentgrowthYoY'])}

        # Create a dictionary to store the rent price growth rates MoM keyed by GEO_ID, replacing NaN with None
        rent_growth_rates_mom = {geo_id: None if np.isnan(growth_rate) else growth_rate for geo_id, growth_rate in zip(df['GEO_ID'], df['rentgrowthMoM'])}

        # Iterate over each feature in the GeoJSON data
        for feature in geojson_data['features']:
            geo_id = feature['properties']['id']

            if geo_id in rent_prices:
                # Update or add the rent price value to the GeoJSON feature properties, formatted without decimals
                feature['properties']['RentPrices'] = int(rent_prices[geo_id])

                if geo_id in rent_growth_rates_yoy:
                    # Update or add the rent price growth rate YoY to the GeoJSON feature properties, formatted with two decimal places
                    feature['properties']['rentgrowthYoY'] = round(rent_growth_rates_yoy[geo_id], 2) if rent_growth_rates_yoy[geo_id] is not None else None
                else:
                    # Set the rent price growth rate YoY to null if there is no corresponding value
                    feature['properties']['rentgrowthYoY'] = None

                if geo_id in rent_growth_rates_mom:
                    # Update or add the rent price growth rate MoM to the GeoJSON feature properties, formatted with two decimal places
                    feature['properties']['rentgrowthMoM'] = round(rent_growth_rates_mom[geo_id], 2) if rent_growth_rates_mom[geo_id] is not None else None
                else:
                    # Set the rent price growth rate MoM to null if there is no corresponding value
                    feature['properties']['rentgrowthMoM'] = None
            else:
                # Set the rent price value and growth rates to null if there is no corresponding value
                feature['properties']['RentPrices'] = None
                feature['properties']['rentgrowthYoY'] = None
                feature['properties']['rentgrowthMoM'] = None

        # Overwrite the existing GeoJSON file with the updated data
        with open('NewBasemapcopy1.geojson', 'w') as file:
            json.dump(geojson_data, file, indent=2)

        logging.info("GeoJSON file updated successfully.")

    except Exception as e:
        logging.error(f"An error occurred during data processing: {e}")

except Exception as e:
    logging.error(f"An error occurred: {e}")