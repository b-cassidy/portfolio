import os
import pandas as pd
import numpy as np
import string
from datetime import datetime, timedelta
import seaborn as sns
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import ccf

# Gather and set direcotory paths for visuals
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
visuals_dir = os.path.join(project_root, 'visuals')
data_dir = os.path.join(project_root, 'data')


def generate_fake_forecasting_data(num_days=1000):
    """
    Function to create sample data to be used with 'incorrect_forecasts_use_case.py'

    Parameters:
    num_days (int): The number of days to create data for (default is 1000)

    Returns 
    pd.Dataframe: A Dataframe containing the generated test data as below;
        'Date': A date column with a range of dates
        'Weekday': String showing the day of the week the date falls on
        'Customer_Count': Number showing how many customers we have at the end of the day
        'Marketing_Budget': Business agreed budget for any marketing activity that day
        'Marketing_Spend': Actual business spend on marketing activity for that day
        'Customer_Quotes': Number of quotes completed on that day on the back of marketing activity
        'Customer_Contacts': Actual number of customer contacts that day into the business
        'Forecast_Contacts': Original forecast of customer contacts that the business has been using historically
        'Average_Handling_Time': Average handling time from the customer contacts
        'Notes': Random notes added to the data by the business

    Note, function also saves a copy of the produced data in a CSV file machine_learning folder.
    """

    # Set function parameters
    csv_file = 'demand_forecasting_ML/data/fake_forecasting_data.csv'
    np.random.seed(42)  # Setting as 42 to help with reproducibility

    # Set date ranges for data and generate date list
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=num_days - 1)
    date_list = pd.date_range(start=start_date, periods=num_days, freq='D')

    # Set the truth for sample date where we see Marketing_Spend drive Customer_Quotes which then drives Customer_Contacts (Both with a lag)
    # Here we see each pound in marketing leads to 0.4 quotes with some extra noise included so this is not perfectly linear
    marketing_spend = np.random.normal(5000, 1000, num_days)
    # here we see each quote generates 0.6 of a customer_contact with some extra random noise so this is not perfectly linear
    customer_quotes = (pd.Series(marketing_spend).shift(
        2) * 0.4) + np.random.normal(500, 50, num_days)

    # Build up customer_base which increases slightly as time goes by as well as the impact that this is having on customer_contacts over time
    customer_base = 20000 + (np.arange(num_days) * 5) + \
        np.random.normal(0, 100, num_days)
    base_impact = 0.04 - (np.arange(num_days) / num_days) * 0.02

    # Calculate actual contacts which is mainly led by marketing_spend and customer_quotes
    customer_contacts = (customer_base * (base_impact / 2)) + \
        (pd.Series(customer_quotes).shift(3) * 0.2) + \
        np.random.normal(50, 10, num_days)

    # Create the legacy forecast values
    forecast_contacts = (customer_base * 0.04)

    # Set other columns which aren't really drivers for customer_contacts
    marketing_budget = marketing_spend * \
        1.05 + np.random.normal(0, 10, num_days).round(2)
    average_handling_time = np.random.uniform(500, 750, num_days)

    # Add in a 'note' to random rows of the data
    notes = []
    char_list = list(string.ascii_letters + string.digits)
    for i in range(num_days):
        if np.random.random() < 0.1:
            # For small percentage of rows add in a random 20 character text string
            ran_string = ''.join(np.random.choice(char_list, size=20))
            notes.append(f'ERR_{ran_string}')
        else:
            notes.append('System_OK')

    # Bring data together into dataframe
    df = pd.DataFrame({
        'Date': date_list, 'Weekday': date_list.strftime('%A'), 'Customer_Count': customer_base, 'Marketing_Budget': marketing_budget, 'Marketing_Spend': marketing_spend, 'Customer_Quotes': customer_quotes, 'Customer_Contacts': customer_contacts, 'Forecasted_Contacts': forecast_contacts, 'Average_Handling_Time': average_handling_time, 'Notes': notes
    })

    # Fill in NaN values in dataframe with column mean value
    df = df.fillna(df.mean(numeric_only=True))

    # Format 'count' columns as integers
    int_cols = ['Customer_Count', 'Customer_Quotes', 'Customer_Contacts',
                'Forecasted_Contacts', 'Average_Handling_Time']
    df[int_cols] = df[int_cols].round().astype(int)

    # Format 'currency' columns to two decimal places
    float_cols = ['Marketing_Budget', 'Marketing_Spend']
    df[float_cols] = df[float_cols].round(2)

    # Write out data to CSV
    df.to_csv(csv_file, index=False)

    # Return data
    return df


def get_high_corr_pairs(df, threshold=0.8):
    """
    Function to check for linear relationships between features in a DataFrame.

    Parameters:
    df (pd.DataFrame): The input DataFrame containing the features to check.
    threshold (float): The correlation threshold above which features are considered to have a strong linear relationship.

    Returns:
    list: A list of tuples containing pairs of features that have a correlation above the specified threshold.
    Including the correlation value for each pair along with a heatmap of the correlation matrix for visual inspection.
    """

    # Calculate the correlation matrix on numerical columns only
    df_numeric = df.select_dtypes(include=[np.number])
    corr_matrix = df_numeric.corr().abs()

    # Create and apply a mask to the upper triangle of the matrix to avoid duplicate eg A-B and B-A
    mask = np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
    upper = corr_matrix.where(mask)

    # Flatten the upper triangle matrix and name columns for clarity
    pairs = (upper.unstack()
             .dropna()
             .reset_index())

    pairs.columns = ['Feature1', 'Feature2', 'Correlation']

    # Filter pairs based on the specified threshold
    pairs = pairs[pairs['Correlation'] >= threshold].copy()

    # Sort pairs by correlation value in descending order
    pairs = pairs.sort_values(
        by='Correlation', ascending=False).reset_index(drop=True)

    return pairs


def plot_corr_heatmap(df):
    """
    Function to plot a heatmap of the correlation matrix for numerical columns in a DataFrame.

    Parameters:
    df (pd.DataFrame): The input DataFrame containing the features to visualize.
    """

    # Calculate the correlation matrix from provided DataFrame
    df_numeric = df.select_dtypes(include=[np.number])

    # Set matplotlib figure size
    plt.figure(figsize=(12, 10))

    # Set up the heatmap
    sns.heatmap(df_numeric.corr(), annot=True,
                fmt=".2f", cmap='coolwarm', center=0)

    # Set title and display the plot
    plt.title('Correlation Heatmap', fontsize=16)

    # Save chart to file
    plt.savefig(os.path.join(visuals_dir, 'correlation_heatmap.png'),
                dpi=300, bbox_inches='tight')

    plt.show()


def check_lagged_corr(df, target_col, max_lag=7, date_col=None, threshold=0.7):
    """
    Function to check for lagged correlations between a target variable and other features in a DataFrame.

    Parameters:
    df (pd.DataFrame): The input DataFrame containing the features and target variable.
    target_col (str): The name of the target variable column.
    max_lag (int): The maximum number of lags to check for correlation (Default is 7).
    date_col (str): The name of the date column, if present, to ensure proper sorting before checking lags.
    threshold (float): The minimum absolute correlation value to consider a lagged correlation significant (Default is 0.7).

    Returns:
    pd.DataFrame: A DataFrame containing the lagged correlation values for each feature with the target variable.
    """

    # If not date_col is provided check the dataframe for the first datetime column and use that for sorting, if no datetime column is found proceed without sorting
    if date_col is None:
        datetime_cols = df.select_dtypes(
            include=['datetime', 'datetime64']).columns
        if len(datetime_cols) > 0:
            date_col = datetime_cols[0]

    # Ensure the DataFrame is sorted by date if a date column is provided
    if date_col:
        df = df.sort_values(by=date_col)

    # Initialize a DataFrame to store lagged correlation results
    lagged_corrs = pd.DataFrame(
        columns=['Target', 'Feature', 'Lag', 'Correlation'])

    # Initialize a list to keep track of features that have correlations above the threshold
    results_list = []

    # Loop through each numerical feature in the DataFrame
    for col in df.select_dtypes(include=[np.number]).columns:
        if col == target_col:
            continue  # Skip the target column itself

        # Calculate lagged correlations for the specified range of lags
        for lag in range(1, max_lag + 1):
            corr_value = ccf(df[target_col], df[col], adjusted=False)[lag]

            # Append the results to the lagged_corrs DataFrame if the correlation value meets the specified threshold
            if abs(corr_value) >= threshold:
                results_list.append({
                    'Target': target_col, 'Feature': col, 'Lag': lag, 'Correlation': corr_value
                })

    # Convert the results list to a DataFrame
    lagged_corrs = pd.DataFrame(results_list)

    # Check if any significant lagged correlations were found
    if lagged_corrs.empty:
        print(
            f'--- No significant lagged correlations found with a minimum threshold of {threshold}')
        return None
    else:
        print(
            f'--- Found {len(lagged_corrs)} significant lagged correlations with minimum threshold {threshold}')

    # Sort the lagged correlations by absolute correlation value in descending order
    lagged_corrs['AbsCorrelation'] = lagged_corrs['Correlation'].abs()
    lagged_corrs = lagged_corrs.sort_values(
        by='AbsCorrelation', ascending=False)
    lagged_corrs = lagged_corrs.drop(
        columns=['AbsCorrelation']).reset_index(drop=True)

    return lagged_corrs


def plot_lagged_correlations(df, target_col, feature_cols, max_lag=15):
    """
    Function to plot the lagged correlation values for a target variable against other features in a DataFrame.

    Parameters:
    df (pd.DataFrame): The input DataFrame containing the features and target variable.
    target_col (str): The name of the target variable column.
    feature_cols (list): List of feature columns to check and display the lagged correlation for
    max_lag (int): The maximum number of lags to check for correlation (Default is 15).

    Returns:
    None: Displays a line plot of lagged correlations for each feature with the target variable.
    """
    # Count number of features provided
    num_features = len(feature_cols)
    if num_features == 0:
        print('!!! No features provided !!!')
        return

    # Set grid layout based on features (1 row for up to three charts, 2 for more etc.)
    cols = min(num_features, 3)
    rows = (num_features + cols - 1) // cols

    # Start creating figures
    fig, axes = plt.subplots(rows, cols, figsize=(
        6 * cols, 5 * rows), squeeze=False)
    axes = axes.flatten()

    # Start looping through data provided
    for i, feature in enumerate(feature_cols):
        ax = axes[i]

        # Clean for specific pair of columns
        clean_df = df[[feature, target_col]].dropna()

        # Calculate cross correlation figures
        ccf_values = ccf(clean_df[target_col], clean_df[feature], adjusted=False)[
            :max_lag + 1]
        lags = np.arange(len(ccf_values))

        # Plotting on specific 'ax'
        ax.bar(lags, ccf_values, color='blue', alpha=0.7)

        # Add in significance thresholds
        conf_levels = 2 / np.sqrt(len(clean_df))
        ax.axhline(y=conf_levels, color='red', linestyle='--', alpha=0.5)
        ax.axhline(y=conf_levels, color='red', linestyle='--', alpha=0.5)
        ax.axhline(y=0, color='black', linewidth=1)

        # Format subplots
        ax.set_title(f'Lag: {feature} vs {target_col}', fontsize=12)
        ax.set_xlabel('Lag (days)')
        ax.set_ylabel('Correlation')
        ax.set_xticks(lags)
        ax.grid(axis='y', alpha=0.3)

    # Hide unused subplots
    for j in range(i + 1, len(axes)):
        axes[j].axis('off')

    plt.tight_layout()

    # Save chart to file
    plt.savefig(os.path.join(visuals_dir, 'lagged_correlations.png'),
                dpi=300, bbox_inches='tight')

    plt.show()
