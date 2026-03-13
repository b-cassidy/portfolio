# Importing data from https://hub.datanorthyorkshire.org/dataset/business-rates using API

# Import libaraies
import certifi
import requests
import pandas as pd
import ssl
import io


# Set variables
api_url = 'https://hub.datanorthyorkshire.org/api/3/action/package_show?id=business-rates'
output_file = 'data/br_data.csv'


def import_business_rates_data():
    """
    Code used to import the business rates data from above using the API.

    Args:
        None

    Returns:
        Pandas dataframe with all available data from API for business rates ready for cleansing

    Note:
        Tested data 2026-03-12 with six avaialble manual downloads from NYC website by counting rows and chekcing final results in df;

        Data rows

        Jan 2026 = 14, 009
        March 2025 = 13, 870
        August 2024 = 13, 844
        April 2024 = 13, 763
        October 2023 = 13, 719
        July 2023 = 13, 891

        TOTAL = 83, 096
    """

    # Handle SSL context to prevent errors when running
    ssL_context = ssl.create_default_context(cafile=certifi.where())

    # Check for response from api
    response = requests.get(api_url, verify=certifi.where(), timeout=10).json()
    if not response['success']:
        return 'Error - could not connect to API'

    # Get available resources and initialise blank df fro data
    resources = response['result']['resources']
    br_df = pd.DataFrame()

    # Loop through available resources
    for res in resources:
        if res['format'].lower() == 'xlsx':
            # Download data
            print(f'--- Fetching: {res['name']} {res['description']}')

            res_content = requests.get(
                res['url'], verify=certifi.where()).content
            df = pd.read_excel(io.BytesIO(res_content))

            # Capture snapshot date from the resource name
            df['snapshot_label'] = res['description']

            # Add data to main br_df
            br_df = pd.concat([br_df, df], ignore_index=True)

    # Return results and update with row_count
    df_count = len(br_df)
    print(f'--- Total rows imported: {df_count}')

    return br_df
