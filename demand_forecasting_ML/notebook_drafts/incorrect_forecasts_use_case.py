"""
Use Case: 
    Optimising resource allocation by revisiting demand forecasting

The Problem:
    The business is seeing the variance between forecasted and actual customer contacts increase.
    This is leading to insufficient staffing, either over-staffing and wasting resources or under 
    staffing and leading to poor customer experience.

The Investigation (so far):
    Early investigations suggest some success has been had on increasing original forecast accuracy
    basing this on a customer count to contacts rate of 4% but since then forecast inaccuracy has 
    increased. For now, forecasts based on the 4% contact rate are still being used until a more 
    accurate forecasting model can be provided.

Objectives:
    1. Review historical forecast methodology and confirm that this is no longer accurate
    2. Analyse existing data to understand what the drivers for customer contact are
    3. Once drivers are known build a machine learning model to deliver more accurate forecasting
"""

# Import
import sys
import os
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_percentage_error

# Adds the root directory to the python path to avoid ModuleNotFoundErrors when running
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Check roots and then import custom functions from utils
if project_root not in sys.path:
    sys.path.append(project_root)
try:
    from utils.portfolio_functions import (
        generate_fake_forecasting_data, get_high_corr_pairs, plot_corr_heatmap, check_lagged_corr, plot_lagged_corr, plot_lagged_correlations
    )
    print("--- Portfolio functions imported successfully")
except ImportError as e:
    print(f"--- Import Error: {e}")
    print(f"---I am looking for 'utils' in: {project_root}")


# ###################################################################
# Objective 1: Getting our business data and validating the problem
# ###################################################################
print('\n' + '='*60)
print('  OBJECTIVE 1: REVIEW HISTORICAL FORECAST METHOD AND CONFIRM THIS IS NO LONGER ACCURATE')
print('='*60 + '\n')

# Generate our business data using generate_fake_forecasting_data function
df_raw = generate_fake_forecasting_data()
df_step1 = df_raw.copy()
print('--- Business data stored in dataframe called df_data')

# Break down the difference between forecast contacts and actual in volume and percentage
# As we are looking at forecast accuracy rather than specifically under/over delivery we
# will look for absolute differences
df_step1['Abs_Variance'] = abs(
    df_step1['Customer_Contacts'] - df_step1['Forecasted_Contacts'])
df_step1['Per_Variance'] = (df_step1['Abs_Variance'] /
                            df_step1['Customer_Contacts']) * 100

# Add in Contact_Rate which is the existing business logic used for forecasting
df_step1['Contact_Rate'] = (
    df_step1['Customer_Contacts'] / df_step1['Customer_Count']) * 100

# Visualise Contact_Rate and Per_Variance over time to validate business problem
plt.figure(figsize=(14, 6))
rolling_days = 28

# Plot Per_variance over time
plt.plot(df_step1['Date'], df_step1['Per_Variance'].rolling(rolling_days).mean(),
         color='red', alpha=0.5, label=f'Forecast Inaccuracy ({rolling_days} day average)')

# Plot Contact_Rate over time
plt.plot(df_step1['Date'], df_step1['Contact_Rate'].rolling(rolling_days).mean(),
         color='blue', alpha=0.5, label=f'Contact Rate ({rolling_days} day average)')

# Format visual
plt.axhline(y=5, color='green', linestyle='--',
            label='Expected Inacuracy (5%)')
plt.title('Legacy Forecasting Performance: Inaccuracy Over Time', fontsize=14)
plt.ylabel('Forecast Inaccuracy & Contact Rate')
plt.xlabel('Date')
plt.legend()
plt.grid(axis='y', alpha=0.3)

# Look at getting the Mean Absolute Percentage Error (MAPE) for different segments of our data to see it change over time
mape_segments = 4
ape = abs(df_step1['Customer_Contacts'] -
          df_step1['Forecasted_Contacts']) / df_step1['Customer_Contacts']

# Set 'Date' as index for easier splitting and plotting
df_step1.set_index('Date', inplace=True)

# Split data into the selected number of segments
split_data = np.array_split(ape.values, mape_segments)
split_indexes = np.array_split(df_step1.index.values, mape_segments)

# Calculate mean for each segment
segment_mape = [segment.mean() * 100 for segment in split_data]

# Print the segment MAPE values with dates
print(
    f'--- Data has been split into {mape_segments} segments to show accuracy change over time')
for i in range(mape_segments):
    segment_start = split_indexes[i][0]
    segment_end = split_indexes[i][-1]
    segment_start_date = pd.to_datetime(segment_start).strftime('%Y-%m-%d')
    segment_end_date = pd.to_datetime(segment_end).strftime('%Y-%m-%d')
    segment_dates = f'{segment_start_date} to {segment_end_date}'
    print(
        f'--- Segment {i+1}: {segment_dates} - MAPE (%) {segment_mape[i].round(2)}')

print('\n' + '--- FINDINGS;')
print('--- As we can see, forecast accuracy is getting worse over time')
print('--- We can now look to create a more accurate model')


# ###################################################################
# Objective 2: Analyse Data to Understand Drivers for Contact
# ###################################################################
print('\n' + '='*60)
print('  OBJECTIVE 2: ANALYSE DATA TO UNDERSTAND DRIVERS FOR CONTACT')
print('='*60 + '\n')

# Reload business data
df_step2 = df_raw.copy()

# Check all available data for correlations
# coefficient of at least +/- 0.5 will show us columns which have a noticeable relationship
corr_threshold = 0.5
df_corr = get_high_corr_pairs(df_step2, corr_threshold)
corr_count = len(df_corr)

# Print results found for correlating columns
if corr_count > 0:
    print(
        f'--- Based on a coefficient of at least {corr_threshold} we can see {len(df_corr)} correlations;')
    print(df_corr)
else:
    print(
        f'--- Based on a coefficient of at least {corr_threshold} we have no correlations')

print('\n' + '--- FINDINGS;')
if any(df_corr['Feature1'].str.contains('Customer_Contacts')):
    print('--- Found high correlation drivers for contacts in data')
    print(df_corr)
else:
    print('--- No strong same-day drivers for contacts found in data')
    print('--- Drivers for contact may be hidden behind a time-lag')

# Results here should show a link between forecasted contacts and customer count which is
# the existing forecasting method and marketing spend/budget. We know from the business
# and above that forecasting based on customer_count is incorrect

# Plot correlation heatmap to confirm results
plot_corr_heatmap(df_step2)


# ###################################################################
# Objective 2-B: Analyse Data to Check for Lagging Correlations
# ###################################################################
print('\n' + '='*60)
print('  OBJECTIVE 2-B: ANALYSE DATA TO CHECK FOR LAGGING CORRELATIONS')
print('='*60 + '\n')

# Review the data we have to see if the correlation coefficients increase if we include a lag
# between our target variable (customer_contacts) and our other features
df_lag = df_raw.copy()
max_lag_days = 10

lag_results = check_lagged_corr(
    df=df_lag, target_col='Customer_Contacts', max_lag=max_lag_days, threshold=corr_threshold)

# Count results and print those that are found
lag_count = len(lag_results)
if lag_count > 0:
    print(f'\n' + f'--- The {lag_count} lagged correlations found are;')
    for i in range(lag_count):
        print(
            f'--- {i+1}. {lag_results.iloc[i]['Feature']} with a {lag_results.iloc[i]['Lag']} day lag and {lag_results.iloc[i]['Correlation'].round(2)} correlation')
else:
    print('--- no lagged correlations found, need more data!')

print('\n' + '--- FINDINGS;')
print('--- We now see a 3 day lag between Customer_Quotes and our target variable of Customer_Contacts')
print('--- We also see a 5 day lag between our target and marketing budget/spend')
print('--- This gives us the information we need to look at building our forecasting model')
print('--- Given how marketing budget is so closely related to marketing spend, we will just')
print('--- look at including marketing budget as a feature in our model to avoid multicollinearity issues')

# Plot lagged correlations
features_to_plot = ['Customer_Quotes', 'Marketing_Spend', 'Marketing_Budget']

plot_lagged_correlations(df=df_lag, target_col='Customer_Contacts',
                         feature_cols=features_to_plot, max_lag=10)


# ###################################################################
# Objective 3 - Build ML Model for More Accurate Forecasting
# ###################################################################
print('\n' + '='*60)
print('  OBJECTIVE 3: BUILD MACHINE LEARNING MODEL FOR MORE ACCURATE FORECASTING')
print('='*60 + '\n')

# Create df_model dataframe, set Date as index for easing joining later and Show original shape of our data
df_model = df_raw.copy()
df_model = df_model.set_index('Date')
print('--- Original shape of data before modelling;')
print(df_model.info())

# Begin to model our data for machine learning, need to create 'lagged' features by 'shifting'
df_model['Customer_Quotes_Lagged'] = df_model['Customer_Quotes'].shift(3)
# df_model['Marketing_Spend_Lagged'] = df_model['Marketing_Spend'].shift(5) # Removed to avoid multicollinearity
df_model['Marketing_Budget_Lagged'] = df_model['Marketing_Budget'].shift(5)

# Shifting will create 'null' values in some rows, drop these now
df_model = df_model.dropna()

# Set new columns to int datatype
int_cols = ['Customer_Quotes_Lagged', 'Marketing_Budget_Lagged']
df_model[int_cols] = df_model[int_cols].round().astype(int)

# Show updated model of data now after changes
print('\n' + '--- Updated shape of data after modelling;')
print(df_model.info())

# Define our features and target for our model
model_features = ['Customer_Count',
                  'Customer_Quotes_Lagged', 'Marketing_Budget_Lagged']
model_target = 'Customer_Contacts'

x = df_model[model_features]
print(
    '\n' + f'--- The following features have been defined for our model to forecast {model_target};')
for i, feature in enumerate(model_features, 1):
    print(f'--- {i}. {feature}')

y = df_model[model_target]

# Split our data for training and testing (80/20)
x_train, x_test, y_train, y_test = train_test_split(
    x, y, test_size=0.2, random_state=42, shuffle=False)

print(
    '\n' + f'--- Data has been split with {len(x_train)} rows for training and {len(x_test)} for testing')

# Initiate the model and begin training
start_time = time.time()
model = LinearRegression()
model.fit(x_train, y_train)

# Begin to make predictions
y_predict = model.predict(x_test)
end_Time = time.time()
training_time = end_Time - start_time
print('\n' + f'--- Model training complete in {training_time:.4f} second(s)')

# Bring in original forecast figures to compare to our new model
df_results = pd.DataFrame(index=x_test.index)
df_results['Actual_Contacts'] = y_test
df_results['ML_Forecast'] = y_predict

# Add in original forecast based on contact rate for comparison
df_results['Business_Forecast'] = df_step1['Forecasted_Contacts']
df_results = df_results.reset_index()

# Calculate mean absolute percentage error for our model and the original business forecast
model_mape = mean_absolute_percentage_error(
    df_results['Actual_Contacts'], df_results['ML_Forecast']) * 100
business_mape = mean_absolute_percentage_error(
    df_results['Actual_Contacts'], df_results['Business_Forecast']) * 100

# Prints results of model vs current methodology
print('--- Forecasting performance on test data using MAPE (lower is better);')
print(f'--- New model has a MAPE on test date of: {model_mape:.2f}%')
print(
    f'--- Original business forecast has a MAPE on test date of: {business_mape:.2f}%')

# Share the weightings from the model to show the importance of different features
feature_importance = pd.DataFrame({
    'Feature': model_features,
    'Coefficient': model.coef_
}).sort_values(by='Coefficient', key=abs, ascending=False)
print('\n' + '--- The following are the weightings for each feature in our model;')
print(feature_importance)

# Plot results to visually compare forecasts
plt.figure(figsize=(14, 6))
plt.plot(df_results['Date'], df_results['Actual_Contacts'],
         label='Actual Contacts', color='black', linestyle='--')
plt.plot(df_results['Date'], df_results['Business_Forecast'],
         label='Business Forecast', color='red')
plt.plot(df_results['Date'], df_results['ML_Forecast'],
         label='ML Forecast', color='blue')

plt.title('Forecast Comparison: ML Model vs Business Forecast')
plt.xlabel('Date')
plt.ylabel('Number of Contacts')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()
