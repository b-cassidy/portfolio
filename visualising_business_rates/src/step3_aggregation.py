# code for creating our aggregated data files for PBI

# gross_br_bill = current value rate * business rate (total that would be paid annually with no discounts)
# net_br_bill = annual amount charged after discounts
# prorata_net_bill = prorata amount charged after discounts based on period length

# Import libaries
import pandas as pd
import numpy as np
import re
from datetime import datetime
from dateutil import parser


def create_summary_fact_table(df):
    """
    Creation of main aggregated summary fact data.

    Args:
        df: dataframe from ingestion and processing

    Returns:
        df: dataframe for our aggregated summary fact table
    """

    # Create cleaned Outcode from address_postcode column
    df['outcode'] = df['address_postcode'].str.split(
        ' ').str[0].str.strip().str.upper()
    df['outcode'] = df['outcode'].fillna('Unknown')

    # Group data by key dimensions
    fact_table = df.groupby(
        ['snapshot_label_date',
         'period_start',
         'period_end',
         'days_in_period',
         'fixed_district',
         'outcode',
         'lifecycle_status',
         'business_sector'
         ]).agg(
        business_count=('occupant_id', 'nunique'),
        annual_gross_br=('gross_br_bill', 'sum'),
        annual_net_br=('net_br_bill', 'sum'),
        prorata_net_br=('prorata_net_bill', 'sum')
    ).reset_index()

    # Rename columns for clarity
    fact_table.rename(columns={
        'fixed_district': 'District', 'snapshot_label_date': 'File Date'
    }, inplace=True)

    # Return dataframe
    return fact_table
