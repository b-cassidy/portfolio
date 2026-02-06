import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import seaborn as sns
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import ccf


def generate_corr_test_data(num_days=5000, random_state=42):
    """
    Fumction to create sample data to test correlation functions on, including both highly correlated and uncorrelated features, as well as a date column to test lagged correlation functions.

    Parameters:
    num_days (int): The number of days to generate for the date column (Default is 5000).
    random_state (int): The random seed for reproducibility (Default is 42).

    Returns:
    pd.DataFrame: A DataFrame containing the generated test data as below;
        'Date': A date column with a range of dates
        'Sales': A numeric target variable with some random noise but will have a high correlation with 'Revenue' and a moderate correlation with 'Ad_Spend'
        'Revenue': A numeric feature that is highly correlated with 'Sales'
        'Ad_Spend': A numeric feature that has a moderate correlation with 'Sales'
        'Customer Contact': A numeric feature that is related to 'Sales' with a lag of 0 and Ad_Spend with a lag of 3 days
        'Region': A categorical feature that is uncorrelated with 'Sales'
        'Complaints': A numeric feature that is uncorrelated with any other feature or the target variable
    csv file of the generated data is also saved to the local directory for use in testing the correlation functions.
    """

    # Set function parameters
    csv_file = "utils/corr_test_data.csv"
    np.random.seed(random_state)

    # Generate a date range for the specified number of days
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=num_days - 1)
    date_list = pd.date_range(start=start_date, periods=num_days, freq='D')

    # Generate base values here to ensure the desired correlations are achieved
    ad_spend = np.random.normal(5000, 500, num_days)
    complaints = np.random.normal(200, 20, num_days)

    # Create the target variable 'Sales' with a moderate correlation to 'Ad_Spend'
    sales = (ad_spend * 0.5) + np.random.normal(0, 50, num_days)

    # Create 'Revenue' with a high correlation to 'Sales'
    revenue = (sales * 1.5) + np.random.normal(0, 10, num_days)

    # Create 'Customer Contact' with a lagged correlation 'Ad_Spend'
    # Need to create and sort our existing data into a temp_df to begin with to ensure the lagged correlation is properly created
    temp_df = pd.DataFrame({
        'Date': date_list,
        'Ad_Spend': ad_spend,
        'Sales': sales,
        'Complaints': complaints,
        'Revenue': revenue
    })
    temp_df = temp_df.sort_values('Date').reset_index(drop=True)

    # Create 'Customer Contact' with a lagged correlation to 'Ad_Spend' (lag of 3 days) and a lag of 0 with 'Sales'
    # For simplicity, contacts = (sales * 0.1) + (ad_spend shifted by 3 days * 0.05)
    temp_df['Customer_Contact'] = (temp_df['Sales'] * 0.1) + (
        temp_df['Ad_Spend'].shift(3) * 0.05) + np.random.normal(0, 5, num_days)

    # Fill in the first 3 rows of 'Customer_Contact' which will have NaN values due to the shift with the mean of contacts
    temp_df['Customer_Contact'] = temp_df['Customer_Contact'].fillna(
        temp_df['Customer_Contact'].mean())

    # Create 'Region' as a categorical feature that is uncorrelated with 'Sales'
    regions = ['North', 'South', 'East', 'West']
    temp_df['Region'] = np.random.choice(regions, size=num_days)

    # Bring final dataframe together with all features and target variable
    df_test = temp_df.copy()

    # Save the generated data to a CSV file for testing purposes
    df_test.to_csv(csv_file, index=False)

    return df_test


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
            print(
                f'--- No date_col provided, using {date_col} for sorting ---')
        else:
            print(
                '--- No date_col provided and no datetime column found, proceeding without sorting ---')

    # Ensure the DataFrame is sorted by date if a date column is provided
    if date_col:
        df = df.sort_values(by=date_col)
        print(f'--- DataFrame sorted by {date_col} ---')

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
            f'--- No significant lagged correlations found with threshold {threshold} ---')
        return None
    else:
        print(
            f'--- Found {len(lagged_corrs)} significant lagged correlations with threshold {threshold} ---')

    # Sort the lagged correlations by absolute correlation value in descending order
    lagged_corrs['AbsCorrelation'] = lagged_corrs['Correlation'].abs()
    lagged_corrs = lagged_corrs.sort_values(
        by='AbsCorrelation', ascending=False)
    lagged_corrs = lagged_corrs.drop(
        columns=['AbsCorrelation']).reset_index(drop=True)

    return lagged_corrs


def plot_lagged_corr(df, feature_col, target_col, max_lag=15):
    """
    Function to plot the lagged correlation values for a target variable against other features in a DataFrame.

    Parameters:
    df (pd.DataFrame): The input DataFrame containing the features and target variable.
    target_col (str): The name of the target variable column.
    max_lag (int): The maximum number of lags to check for correlation (Default is 7).
    date_col (str): The name of the date column, if present, to ensure proper sorting before checking lags.

    Returns:
    None: Displays a line plot of lagged correlations for each feature with the target variable.
    """

    # Clean provided dataframe
    clean_df = df[[feature_col, target_col]].dropna()

    # Calculate cross correlation figures (lagged correlations) for the specified feature and target variable
    ccf_values = ccf(clean_df[target_col], clean_df[feature_col], adjusted=False)[
        :max_lag + 1]

    # Start to plot the ccf_values
    plt.figure(figsize=(12, 6))
    lags = np.arange(len(ccf_values))
    plt.bar(lags, ccf_values, color='skyblue', edgecolor='navy', alpha=0.7)

    # Add thresholds for significance (2 / sqrt(n)) where n is the number of observations, to help identify significant correlations
    conf_levels = 2 / np.sqrt(len(clean_df))
    plt.axhline(y=conf_levels, color='red',
                linestyle='--', label='Confidence Level')
    plt.axhline(y=-conf_levels, color='red', linestyle='--')
    plt.axhline(y=0, color='black', linewidth=1)

    # Formatting the plot
    plt.title(
        f'Lagged Correlation between {feature_col} and {target_col}', fontsize=14)
    plt.xlabel('Lag (Days)', fontsize=12)
    plt.ylabel('Correlation', fontsize=12)
    plt.xticks(lags)
    plt.legend()
    plt.grid(axis='y', alpha=0.3)

    plt.show()


def pretty_print(df, title):
    """
    Prints a dataframe with a clear header and formatting for the terminal.
    """
    print(f"\n{'='*60}")
    print(f"  {title.upper()}")
    print(f"{'='*60}")

    if df.empty:
        print("  No significant results found.")
    else:
        print(df.to_string(index=False))

    print(f"{'='*60}\n")
