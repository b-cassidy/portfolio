# Sample file using pandas sql for telephony data aggregating and matplotlib for visualization

# need to install pandas, pandasql, matplotlib

import pandas as pd
import pandasql as ps
from pandasql import sqldf
import matplotlib.pyplot as plt

# Class attrributes for file paths
SAMPLE_FILE = 'telephony_data/sample_telephony.csv'
EMPLOYEE_FILE = 'telephony_data/sample_employee.csv'

# Import telephony data into DataFrame
sample_df = pd.read_csv(SAMPLE_FILE)
employee_df = pd.read_csv(EMPLOYEE_FILE)

# SQL query to aggregate call data and get total figures per day, queue, and call status
query = """
    SELECT 
        CallDate
        , QueueName
        , CallStatus
        , COUNT(*) as total_calls
        , SUM(TimeInQueue) as total_queue_time
        , SUM(HandleTime) as total_handle_time
        , CASE
            WHEN CallStatus = 'Abandoned' THEN NULL
            ELSE SUM(HandleTime) / COUNT(*)
          END as avg_handle_time
    FROM
        sample_df
    GROUP BY
        CallDate
        , QueueName
        , CallStatus
    """

# Store first aggregated figures as a DataFrame
agg_df = ps.sqldf(query, locals())


# print(agg_df)

# aggregated_df = ps.sqldf(query, locals())

""" class TelephonyDataProcessor:
"""     """
    Takes the sample telephony call data and performs SQL-based aggregation.

    These aggregations will show insights such as total calls by type, average handling time and abandonment rates over time.
    Will also visualize the results using matplotlib.
    """ """

    # --- Configuration Constants (Class Attributes) ---
    SAMPLE_FILE: str = 'telephony_data/sample_telephony.csv'
    EMPLOYEE_FILE: str = 'telephony_data/sample_employee.csv'

    def __init__(self):
        """
"""         Initializes the telephony data processor. """
"""
        print("Initializing TelephonyDataProcessor...")


    def pull_data(self):
"""         """
        Pulls telephony call and employee data from CSV files into DataFrames.
        """ """
        print("Pulling telephony data from CSV files...")
        self.call_data = pull_telephony_data(self.SAMPLE_FILE)
        print(f"Loaded {len(self.call_data)} call records.")
        print("Pulling employee data from CSV files...")
        self.employee_data = pull_telephony_data(self.EMPLOYEE_FILE)
        print(f"Loaded {len(self.employee_data)} employee records.")

# Pull telephony data from CSV files
def pull_telephony_data(call_data_path):
    call_data = pd.read_csv(call_data_path)
    return call_data

# Aggregate call data using SQL queries


def aggregate_call_data(call_data):
    query = """
"""     SELECT 
        call_type,
        COUNT(*) AS total_calls,
        SUM(call_duration) AS total_duration,
        AVG(call_duration) AS avg_duration
    FROM call_data
    GROUP BY call_type """
"""
aggregated_data = ps.sqldf(query, locals())
    return aggregated_data

# Visualize aggregated call data


def visualize_call_data(aggregated_data):
    fig, ax = plt.subplots(1, 2, figsize=(12, 6))

    # Bar chart for total calls by call type
    ax[0].bar(aggregated_data['call_type'],
              aggregated_data['total_calls'], color='skyblue')
    ax[0].set_title('Total Calls by Call Type')
    ax[0].set_xlabel('Call Type')
    ax[0].set_ylabel('Total Calls')

    # Bar chart for average call duration by call type
    ax[1].bar(aggregated_data['call_type'],
              aggregated_data['avg_duration'], color='salmon')
    ax[1].set_title('Average Call Duration by Call Type')
    ax[1].set_xlabel('Call Type')
    ax[1].set_ylabel('Average Duration (seconds)')

    plt.tight_layout()
    plt.show() """
