# Import libraries
import os
import sys

from utils.demand_forecasting_functions import generate_fake_forecasting_data
from src.stages import run_objective_1, run_objective_2, run_objective_3


def main():
    """
    Main execution script for the 'Demand Forecasting with Machine Learning' business case in this repository. 
    This script controls the flow of our generated business data through generation, analysis, modelling and evaluation.
    """

    print('\n' + '='*100)
    print('  DEMAND FORECASTING WITH MACHINE LEARNING: PROJECT STARTING')
    print('='*100)

    # Step 0: Generate our fake data for this project using the generate_fake_forecasting_data function in utils/demand_forecasting_functions.py
    df_raw = generate_fake_forecasting_data()
    print('\n' + 'Sample data successfully generated')

    # Step 1: Review legacy forecasting method and confirm this is no longer accurate
    df_validated = run_objective_1(df_raw)

    # Step 2: Analyse the data to discover the drivers for customer contacts
    contact_drivers = run_objective_2(df_validated)
    print(
        '\n' + f'Data analysied drivers for customer contacts are; {contact_drivers}')

    # Step 3: New drivers identified look to build a new forecasting model using sklearn and evaluate the performance uplift against the legacy method
    final_results = run_objective_3(df_raw, contact_drivers)

    print('\n' + '='*100)
    print('  DEMAND FORECASTING WITH MACHINE LEARNING: PROJECT COMPLETE')
    print('='*100)

    # Return final results as output in terminal
    print('\n' + 'Final results from new forecasting model:')
    print(final_results.head())


if __name__ == "__main__":
    main()
