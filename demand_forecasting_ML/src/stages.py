# Import needed functions and libraries
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_percentage_error

# Import custom functions from utils (demand_forecasting_functions.py)
from utils.demand_forecasting_functions import (
    plot_corr_heatmap, check_lagged_corr, plot_lagged_correlations
)

# Gather and set direcotory paths for visuals
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
visuals_dir = os.path.join(project_root, 'visuals')


def run_objective_1(df_raw):
    """Review legacy methodology and validate the problem."""
    print('\n' + '='*100)
    print('  OBJECTIVE 1: REVIEW HISTORICAL FORECAST METHOD AND CONFIRM THIS IS NO LONGER ACCURATE')
    print('='*100)

    df = df_raw.copy()

    # Start to calculate original forecast inaccuracy and contact rate
    df['Abs_Variance'] = abs(df['Customer_Contacts'] -
                             df['Forecasted_Contacts'])
    df['Per_Variance'] = (df['Abs_Variance'] / df['Customer_Contacts']) * 100
    df['Contact_Rate'] = (df['Customer_Contacts'] / df['Customer_Count']) * 100

    # Visualise the inaccuracy over time with a rolling average to show trends more clearly
    plt.figure(figsize=(14, 6))
    rolling_days = 28
    plt.plot(df['Date'], df['Per_Variance'].rolling(rolling_days).mean(
    ), color='red', alpha=0.5, label=f'Inaccuracy ({rolling_days}d Avg)')
    plt.plot(df['Date'], df['Contact_Rate'].rolling(rolling_days).mean(
    ), color='blue', alpha=0.5, label=f'Contact Rate ({rolling_days}d Avg)')
    plt.axhline(y=4, color='green', linestyle='--',
                label='Business Forecast Contact Rate (4%)')
    plt.title('Legacy Performance: Forecast Inaccuracy Over Time')
    plt.ylabel('Percentage (%)')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Reminder to review the visual and confirm by key press to continue with code execution
    print('--- ACTION: Please review the Legacy Performance chart (close visual when done)')
    plt.savefig(os.path.join(
        visuals_dir, 'legacy_performance_chart.png'), dpi=300, bbox_inches='tight')
    plt.show()
    input('--- Press Enter to continue with execution...' + '\n')

    # Split the data into segments to show the mean absolute percentage error (MAPE) in each segment
    # to confirm if this inaccuracy is in fact getting worse over time
    mape_segments = 4
    ape = abs(df['Customer_Contacts'] - df['Forecasted_Contacts']
              ) / df['Customer_Contacts']
    split_data = np.array_split(ape.values, mape_segments)

    print(
        f'--- Data split into {mape_segments} segments to show accuracy decay:')
    for i, segment in enumerate(split_data, 1):
        print(f'--- Segment {i}: MAPE {segment.mean()*100:.2f}%')

    return df


def run_objective_2(df_raw):
    """Analyse data to discover the drivers for customer contacts."""
    print('\n' + '='*100)
    print('  OBJECTIVE 2: ANALYSE DATA TO UNDERSTAND DRIVERS FOR CONTACT')
    print('='*100)

    # Reminder to review the visual
    print('--- ACTION: Please review the Correlation Heatmap chart (close visual when done)')

    # Plot correlations between all columns in the data to find the highest correlating features to the target variable (Customer_Contacts)
    plot_corr_heatmap(df_raw)

    # and confirm by key press to continue with code execution
    input('--- Press Enter to continue with execution...' + '\n')

    # No strong same-day correlations so look at a lagged correlations
    lag_results = check_lagged_corr(
        df_raw, target_col='Customer_Contacts', max_lag=10)

    # Reminder to review the visual
    print('--- ACTION: Please review the Lagged Correlation chart (close visual when done)')

    # Plot the lagged correlations using another custom function
    features_to_plot = ['Customer_Quotes',
                        'Marketing_Spend', 'Marketing_Budget']
    plot_lagged_correlations(df_raw, 'Customer_Contacts', features_to_plot)

    # and confirm by key press to continue with code execution
    input('--- Press Enter to continue with execution...' + '\n')

    # Return the identified best lags for the model
    # Three are three lagged correlations plotted but only two are strong and non-multicollinear, so we will return those for the model to use
    # (hardcoded here for simplicity but could be automated to pull the max correlation lag for each feature)
    return {"quotes_lag": 3, "budget_lag": 5}


def run_objective_3(df_raw, lags):
    """Train ML model and compare new forecast to the legacy."""
    print('\n' + '='*100)
    print('  OBJECTIVE 3: BUILD MACHINE LEARNING MODEL FOR MORE ACCURATE FORECASTING')
    print('='*100)

    # Reset the index on the df to date to make joins simpler in teh future
    df_model = df_raw.copy().set_index('Date')

    # Create our lagged features based on the findings from run_objective_2 and drop any rows with null values (due to the lagging)
    # Reminder - not including Marketing_Budget lagged
    df_model['Quotes_Lagged'] = df_model['Customer_Quotes'].shift(
        lags['quotes_lag'])
    df_model['Budget_Lagged'] = df_model['Marketing_Budget'].shift(
        lags['budget_lag'])
    df_model = df_model.dropna()

    # Start preparing the data for the model by selecting our features and target variable
    features = ['Customer_Count', 'Quotes_Lagged', 'Budget_Lagged']
    X = df_model[features]
    y = df_model['Customer_Contacts']

    # Split our data into train and test sets on an 80/20 split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False)

    # Begin our model training and show time taken for this
    start_time = time.time()
    model = LinearRegression()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    # Round predictions to nearest whole number as we can't have fractional contacts
    y_pred = np.round(y_pred).astype(int)

    print(f"--- Model Training Time: {time.time() - start_time:.4f} seconds")

    # Show the weighting of our selected features in the model (coefficients in the case of linear regression)
    importance = pd.DataFrame({'Feature': features, 'Weight': model.coef_})
    print("\n--- Feature Importance (Coefficients):")
    print(importance.to_string(index=False))

    # Start to bring our predictions and older business forecasts together to compare the accuracy of the two methods
    df_results = pd.DataFrame(index=X_test.index)
    df_results['Actual_Contacts'] = y_test
    df_results['ML_Forecast'] = y_pred
    df_results['Legacy_Forecast'] = df_raw.set_index(
        'Date').loc[X_test.index, 'Forecasted_Contacts']

    # Compare the accuracy of the two methods using mean absolute percentage error (MAPE) and print out a scorecard to show the results
    ml_mape = mean_absolute_percentage_error(
        df_results['Actual_Contacts'], df_results['ML_Forecast']) * 100
    biz_mape = mean_absolute_percentage_error(
        df_results['Actual_Contacts'], df_results['Legacy_Forecast']) * 100

    print(f"\n--- Scorecard (Test Data) ---")
    print(f"Business Legacy MAPE: {biz_mape:.2f}%")
    print(f"ML Model MAPE:        {ml_mape:.2f}%")

    # Plot the results to show the difference in accuracy using our test data plotting model &  legacy forecasts against the actuals
    plt.figure(figsize=(14, 6))
    plt.title('Actual Contacts vs Legacy & ModelForecasts')
    plt.plot(df_results.index, df_results['Actual_Contacts'],
             label='Actual Contacts', color='black', linestyle='--')
    plt.plot(df_results.index, df_results['Legacy_Forecast'],
             label='Legacy Forecast', color='red', linestyle='-')
    plt.plot(df_results.index, df_results['ML_Forecast'],
             label='Model Forecast', color='green', linestyle='-')
    plt.xlabel('Date')
    plt.ylabel('Contact Volumes')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Reminder to review the visual and confirm by key press to continue with code execution
    print('--- ACTION: Please review the Legacy vs Model Forecast chart (close visual when done)')
    plt.savefig(os.path.join(visuals_dir, 'new_performance_chart.png'),
                dpi=300, bbox_inches='tight')
    plt.show()
    input('--- Press Enter to continue with execution...' + '\n')

    return df_results
