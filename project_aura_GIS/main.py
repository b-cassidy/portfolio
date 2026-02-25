# Import libaries
import os
import sys

# Import custom functions
from utils.project_aura_functions import extract_max_year, assign_age_risk, assign_keyword_risk, assign_imd_risk
from src.step_01_ingestion import data_ingestion
from src.step_02_processing import data_processing
from src.step_03_analysis import data_analysis

# Set variables
raw_data_path = 'project_aura_GIS/data/raw'
processed_data_path = 'project_aura_GIS/data/processed'


def main():
    """
    Main execution script for the 'Project Aura GIS' business case in this repository. 
    This script controls the flow of our generated business data through ingestion, processing, analysis and output.
    """
    # Project startaaaaaaa
    print('\n' + '='*100)
    print('  PROJECT AURA GIS: PROJECT STARTING')
    print('='*100)

    # Step 1: Ingest our data from the data/raw folder and perform initial cleaning and merging to create data/processed files
    print('\n' + '='*100)
    print('  STEP 1: DATA INGESTION')
    print('='*100 + '\n')
    # data_ingestion(raw_data_path, processed_data_path)

    # Step 2: Process the ingested data to create risk scores for each property based on their characteristics and location
    print('\n' + '='*100)
    print('  STEP 2: DATA PROCESSING')
    print('='*100 + '\n')
    risk_df = data_processing(processed_data_path)

    # Step 3: Analyse the processed data to identify trends and insights around energy efficiency risk across different property types and locations
    print('\n' + '='*100)
    print('  STEP 3: DATA ANALYSIS')
    print('='*100 + '\n')
    data_analysis(risk_df, processed_data_path)

    # Project end
    print('\n' + '='*100)
    print('  PROJECT AURA GIS: PROJECT COMPLETE')
    print('='*100)


if __name__ == "__main__":
    main()
