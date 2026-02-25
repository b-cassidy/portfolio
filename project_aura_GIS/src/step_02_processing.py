# Import libraries
import os
import sys
from utils.project_aura_functions import extract_max_year, assign_age_risk, assign_keyword_risk, assign_imd_risk
import pandas as pd


def data_processing(processed_data_path):
    """
    Process the ingested data to create risk scores for each property based on their characteristics and location.
    """

    # Rules and Weights for construction age band risk scoring
    # Generally, older constructions carry a higher risk of energy inefficiency and higher costs to heat etc.
    age_risk = [
        {'year_max': 1899, 'label': 'Pre 1900', 'score': 3},
        {'year_max': 1949, 'label': 'Interwar', 'score': 2},
        {'year_max': 1975, 'label': 'Post war', 'score': 1},
        {'year_max': 9999, 'label': 'Modern', 'score': 0}
    ]

    # Keyword based scoring adjustments for floor descriptions
    # Specific keywords found in the floor construction description could increase the risk score
    floor_risk = [
        # Suspended floors can have higher risk due to potential for air leakage and heat loss
        {'keyword': 'suspended', 'score': 1},
        # Solid floors are generally more energy efficient (neutral)
        {'keyword': 'no insulation', 'score': 1},
        {'keyword': 'solid', 'score': 0},
        {'keyword': 'insulated', 'score': -1}
    ]

    # Keyword based scoring adjustments for wall descriptions
    # Specific keywords found in the wall construction description could increase the risk score
    wall_risk = [
        # Large impact to energy efficiency
        {'keyword': 'no insulation', 'score': 2},
        # Cavity walls can be more energy efficient (neutral)
        {'keyword': 'solid brick', 'score': 1},
        {'keyword': 'cavity', 'score': 0},
        {'keyword': 'insulated', 'score': -1}
    ]

    # Risk factor based on current EPC rating
    # The current energy rating of the property can be a strong indicator of its overall energy efficiency and potential risk
    epc_risk = {
        'A': 0,
        'B': 0,
        'C': 0,
        'D': 1,
        'E': 2,
        'F': 3,
        'G': 3
    }

    # Risk factor based on IMD (Index of Multiple Deprivation) Decile
    # An areas deprivation level can act as a proxy for potential fuel-poverty
    # FYI IMD Decile of 1 shows most deprived 10% of LSOAs, while a decile of 10 shows least deprived 10% of LSOAs
    imd_risk = [
        {'decile_max': 2, 'score': 2},  # Most deprived areas
        {'decile_max': 4, 'score': 1},  # Moderately deprived areas
        {'decile_max': 10, 'score': 0}
    ]

    # Load the processed data from the previous step
    print('--- Loading processed data ---')
    epc_df = pd.read_csv(os.path.join(processed_data_path, 'filtered_epc.csv'))
    imd_df = pd.read_csv(os.path.join(processed_data_path, 'filtered_imd.csv'))

    # Remove duplicate epc data using BUILDING_REFERENCE_NUMBER as unique property reference
    print('--- Removing all but latest EPC data per property ---')
    epc_df['INSPECTION_DATE'] = pd.to_datetime(
        epc_df['INSPECTION_DATE'])  # Format INSPECTION_DATE as date
    epc_df = epc_df.sort_values(
        by=['BUILDING_REFERENCE_NUMBER', 'INSPECTION_DATE'], ascending=[True, False])

    # Drop all but 'top' (latest) record per BUILDING_REFERENCE_NUMBER
    epc_df = epc_df.drop_duplicates(
        subset='BUILDING_REFERENCE_NUMBER', keep='first')

    # Start apoplying risk scoring functions to the processed dataframe
    print('--- Applying risk scoring functions ---')

    # Extract the maximum construction year from epc data
    epc_df['max_year'] = epc_df['CONSTRUCTION_AGE_BAND'].apply(
        extract_max_year)

    # Apply age risk scoring based on maximum construction year
    epc_df['age_risk'] = epc_df['max_year'].apply(
        lambda x: assign_age_risk(x, age_risk))

    # Apply keyword based risk scoring for floor and wall descriptions
    epc_df['floor_risk'] = epc_df['FLOOR_DESCRIPTION'].apply(
        lambda x: assign_keyword_risk(x, floor_risk))
    epc_df['wall_risk'] = epc_df['WALLS_DESCRIPTION'].apply(
        lambda x: assign_keyword_risk(x, wall_risk))

    # Apply risk scoring based on current EPC rating
    epc_df['epc_risk'] = epc_df['CURRENT_ENERGY_RATING'].map(epc_risk)

    # Apply IMD risk scoring based on IMD decile
    imd_df['imd_risk'] = imd_df['IMD_DECILE'].apply(
        lambda x: assign_imd_risk(x, imd_risk))

    # Merge the EPC and IMD dataframes on the LSOA code
    merged_df = pd.merge(epc_df, imd_df[['LSOA_CODE', 'LOCAL_AUTHORITY_NAME',
                         'imd_risk']], left_on='lsoa21cd', right_on='LSOA_CODE', how='left')

    # Fill any NaN values
    merged_df['imd_risk'] = merged_df['imd_risk'].fillna(0)

    # Calculate a total risk score by summing the individual risk factors
    print('--- Adding final overall risk score to each property ---')
    merged_df['total_risk_score'] = merged_df['age_risk'] + merged_df['floor_risk'] + \
        merged_df['wall_risk'] + merged_df['epc_risk'] + merged_df['imd_risk']

    # Drop duplicate LSOA_CODE column
    merged_df = merged_df.drop(columns=['LSOA_CODE'])

    # Convert all risk columns to int64
    risk_cols = ['age_risk', 'floor_risk', 'wall_risk',
                 'epc_risk', 'imd_risk', 'total_risk_score']
    merged_df[risk_cols] = merged_df[risk_cols].astype('int64')

    # Write out property data with risk score to CSV
    print('--- Writing out property data to processed data folder ---')
    output_file = os.path.join(processed_data_path, 'final_scores.csv')
    merged_df.to_csv(output_file, index=False)

    # Success message
    print('--- Data processing complete ---')

    # Return merged_df so results stay in memory for step 3
    return merged_df
