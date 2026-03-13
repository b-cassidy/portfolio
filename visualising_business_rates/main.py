# Import libaries
import pandas as pd
import os
import sys

# Import custom functions
from utils.business_rates_functions import parse_date_names
from utils.business_rates_functions import extract_postcode
from utils.business_rates_functions import standardise_districts
from utils.business_rates_functions import calculate_rates
from utils.business_rates_functions import apply_prorata_logic
from utils.business_rates_functions import clean_business_categories

# Import src scripts
from src.step1_importing import import_business_rates_data
from src.step3_aggregation import create_summary_fact_table

# Set variables
imported_data_path = 'data/br_imported.csv'
summary_fact_file = 'data/br_summary_fact.csv'
dim_geo_file = 'data/br_dim_geo.csv'
dim_sectors_file = 'data/br_dim_sectors.csv'
dim_calendar_file = 'data/br_dim_calendar.csv'


def main():
    """
    Main execution script for importing and processing the business rates data from North Yorkshire Council
    """

    # Project start
    print('\n' + '='*100)
    print('  VISUALISING BUSINESS RATES: PROJECT STARTING')
    print('='*100)

    # Step 1: Import the business rates data
    print('\n' + '='*100)
    print('  STEP 1: DATA INGESTION')
    print('='*100 + '\n')
    df = import_business_rates_data()

    # Step 2: Clean up the data provided
    print('\n' + '='*100)
    print('  STEP 2: DATA CLEANING & ENRICHMENT')
    print('='*100 + '\n')

    # Apply custom function to get dates from the 'snapshot_label' column
    print('--- Add date field to track changes over time')
    df['snapshot_label_date'] = df['snapshot_label'].apply(parse_date_names)

    # Apply custom function to get postcode from the 'Full Property Address' column
    print('--- Extract postcodes from address details')
    df['address_postcode'] = df['Full Property Address'].apply(
        extract_postcode)

    # Add in standardised districts
    print('--- Fixing district values in the imported data')
    df = standardise_districts(df)

    # Add in example gross and net business rate values
    print('--- Calculating example gross and net business rates')
    df = calculate_rates(df)

    # Add in 'lifecyle_status' to our data
    print('--- Checking business lifecycle statuses')
    df = apply_prorata_logic(df)

    # Clean and enrich business descriptions
    print('--- Checking and cleaning business descriptions')
    df = clean_business_categories(df)

    # Store imported data
    print('--- Saving imported data to CSV')
    os.makedirs(os.path.dirname(imported_data_path), exist_ok=True)
    df.to_csv(imported_data_path)

    # Step 3: Create aggregated data files for PBI
    print('\n' + '='*100)
    print('  STEP 3: DATA AGGREGATION AND EXPORT')
    print('='*100 + '\n')

    # Create summary fact table
    print('--- Creating summary fact table')
    fact_df = create_summary_fact_table(df)
    os.makedirs(os.path.dirname(summary_fact_file), exist_ok=True)
    fact_df.to_csv(summary_fact_file)

    # Create br_dim_geography table
    print('--- Creating geography dimension table')
    dim_geo = fact_df[['District', 'outcode']
                      ].drop_duplicates().reset_index(drop=True)
    os.makedirs(os.path.dirname(dim_geo_file), exist_ok=True)
    dim_geo.to_csv(dim_geo_file, index=False)

    # Create br_dim_sector table
    print('--- Creating sector dimension table')
    dim_sector = pd.DataFrame(
        {'business_sector': fact_df['business_sector'].unique()})
    os.makedirs(os.path.dirname(dim_sectors_file), exist_ok=True)
    dim_sector.to_csv(dim_sectors_file, index=False)

    # Create br_dim_calendar table
    print('--- Creating calendar dimension table')
    # Get dates and date ranges
    min_date = pd.to_datetime(fact_df['File Date']).min()
    max_date = pd.to_datetime(fact_df['File Date']).max()
    all_dates = pd.date_range(min_date, max_date, freq='D')
    # Start building up table
    dim_calendar = pd.DataFrame({'Date': all_dates})
    dim_calendar['Year'] = dim_calendar['Date'].dt.year
    dim_calendar['Quarter'] = dim_calendar['Date'].dt.quarter
    dim_calendar['Month'] = dim_calendar['Date'].dt.month_name()
    dim_calendar['Month_Num'] = dim_calendar['Date'].dt.month
    # Write out file
    os.makedirs(os.path.dirname(dim_calendar_file), exist_ok=True)
    dim_calendar.to_csv(dim_calendar_file, index=False)

    # Project End
    print('\n' + '='*100)
    print('  VISUALISING BUSINESS RATES: PROJECT COMPLETE')
    print('='*100)


if __name__ == "__main__":
    main()
