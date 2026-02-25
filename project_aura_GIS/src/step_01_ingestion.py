# Import libraries
import zipfile
import glob
import pandas as pd
import os
import geopandas as gpd


def data_ingestion(raw_data_path, processed_data_path):
    """
    Ingest raw data, perform initial cleaning, and save processed data for future use.
    """

    # Load postcode lookup data
    print('--- Loading postcode lookup data ---')
    postcode_file = os.path.join(
        raw_data_path, 'PCD_OA21_LSOA21_MSOA21_LAD_NOV25_UK_LU.csv')
    postcode_df = pd.read_csv(postcode_file, low_memory=False)

    # Select columns to keep from postcode data
    postcode_cols = ['pcds', 'lsoa21cd']
    postcode_df = postcode_df[postcode_cols]

    # Load EPC (Energy Performance Certificate) data from csv files wtihin zip folders
    print('--- Loading EPC data ---')
    zip_folders = glob.glob(os.path.join(raw_data_path, 'domestic*.zip'))
    epc_list = []  # Create an empty list to store dataframes

    # Loop through each zip folder, extract the csv file, and load into epc_list
    for zip_folder in zip_folders:
        try:
            with zipfile.ZipFile(zip_folder, 'r') as z:
                # Find the csv file within the zip folder
                csv_files = [f for f in z.namelist(
                ) if f.endswith('certificates.csv')]
                if csv_files:
                    with z.open(csv_files[0]) as f:
                        df = pd.read_csv(f, low_memory=False)
                        epc_list.append(df)
                else:
                    print(
                        f"-ERROR- No certificates.csv found in {zip_folder} -ERROR-")
        except Exception as e:
            print(f"-ERROR- Failed to process {zip_folder}: {e} -ERROR-")

    # Concatenate all dataframes in epc_list into a single dataframe
    if epc_list:
        epc_df = pd.concat(epc_list, ignore_index=True)
        print(
            f"--- Successfully loaded EPC data with {len(epc_df)} records ---")
    else:
        print("-ERROR- No EPC data loaded -ERROR-")

    # Select columns to keep from EPC data
    epc_cols = ['LMK_KEY', 'INSPECTION_DATE', 'ADDRESS1', 'POSTCODE', 'BUILDING_REFERENCE_NUMBER', 'CURRENT_ENERGY_RATING',
                'POTENTIAL_ENERGY_RATING', 'LOCAL_AUTHORITY', 'CONSTRUCTION_AGE_BAND',
                'FLOOR_DESCRIPTION', 'WALLS_DESCRIPTION']
    epc_df = epc_df[epc_cols]

    # Claen up postcode values ahead of join
    epc_df['POSTCODE_cleaned'] = epc_df['POSTCODE'].str.replace(
        ' ', '').str.upper()
    postcode_df['pcds_cleaned'] = postcode_df['pcds'].str.replace(
        ' ', '').str.upper()

    # Join EPC data with postcode lookup to get LSOA codes
    epc_df = epc_df.merge(
        postcode_df, left_on='POSTCODE_cleaned', right_on='pcds_cleaned', how='left')
    epc_df = epc_df.drop(columns=['POSTCODE_cleaned', 'pcds', 'pcds_cleaned'])

    # Load IMD (Index of Multiple Deprivation) data
    print('--- Loading IMD data ---')
    imd_file = os.path.join(
        raw_data_path, 'File_1_IoD2025_Index_of_Multiple_Deprivation.xlsx')
    imd_df = pd.read_excel(imd_file, sheet_name='IMD25')

    # Filter IMD data to keep only data where 'Local Authority District code' matches 'LOCAL_AUTHORITY' values from EPC data
    imd_df = imd_df[imd_df['Local Authority District code (2024)'].isin(
        epc_df['LOCAL_AUTHORITY'].unique())].copy()

    # Select columns to keep from IMD data
    imd_cols = ['LSOA code (2021)', 'Local Authority District name (2024)', 'Index of Multiple Deprivation (IMD) Rank (where 1 is most deprived)',
                'Index of Multiple Deprivation (IMD) Decile (where 1 is most deprived 10% of LSOA']
    imd_df = imd_df[imd_cols]

    # Rename columns for clarity
    imd_df.rename(columns={
        'LSOA code (2021)': 'LSOA_CODE',
        'Local Authority District name (2024)': 'LOCAL_AUTHORITY_NAME',
        'Index of Multiple Deprivation (IMD) Rank (where 1 is most deprived)': 'IMD_RANK',
        'Index of Multiple Deprivation (IMD) Decile (where 1 is most deprived 10% of LSOA': 'IMD_DECILE'
    }, inplace=True)

    # Save processed data to csv files for future use
    print('--- Saving processed data ---')
    epc_df.to_csv(os.path.join(processed_data_path,
                  'filtered_epc.csv'), index=False)
    imd_df.to_csv(os.path.join(processed_data_path,
                  'filtered_imd.csv'), index=False)

    # Load shape data for boundaries and plotting
    print('--- Loading boundary shape data ---')
    shapefile_path = os.path.join(raw_data_path, 'LSOA_2021_EW_BFC_V10.shp')
    shapefile = gpd.read_file(shapefile_path)

    # Filter shapefile to keep only area in the imported EPC data
    shapefile = shapefile[shapefile['LSOA21CD'].isin(
        epc_df['lsoa21cd'].unique())]

    # Simplify shape geometry to keep reduce file size
    print('--- Simplifying boundary shape data ---')
    shapefile['geometry'] = shapefile['geometry'].simplify(
        0.0001, preserve_topology=True)

    # Save processed shapefile
    print('--- Saving boundary shape data ---')
    shapefile.to_file(os.path.join(processed_data_path,
                      'project_aura_lsoas.geojson'), driver='GeoJSON')

    # Success message
    print('--- Data ingestion complete ---')


"""
# Run the data ingestion function when this script is executed directly
if __name__ == "__main__":
    print(f"DEBUG: Current Working Directory is: {os.getcwd()}")
    # Tweak file paths as needed when running the script from here rather than from main.py
    #data_ingestion('../data/raw', '../data/processed')
    """
