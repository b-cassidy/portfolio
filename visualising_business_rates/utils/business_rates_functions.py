import pandas as pd
import numpy as np
import re
from datetime import datetime
from dateutil import parser
# import logging


def parse_date_names(date_string: str) -> str:
    """
    Custom function to be used with North Yorkshire Council API data.

    Args:
    name_string: The resource description string usually in the MMM YY format 

    Returns:
    A string date in 'YYYY-MM-DD' format
    """

    # Remove any leading or trailing spaces in string provided
    data_string = date_string.strip()

    # Extract Month and Year from date string
    match = re.search(r'([a-zA-Z]+)\s*(\d{2,4})$', data_string)

    if match:
        month_part = match.group(1)
        year_part = match.group(2)

        # Standardise 2 digit years
        if len(year_part) == 2:
            year_part = f'20{year_part}'

        # Build up 'Day Month Year' string
        string_date = f'01 {month_part} {year_part}'

        # Attempt to parse the string date
        try:
            parsed_date = parser.parse(string_date)
            return parsed_date.strftime('%Y-%m-%d')

        except Exception:
            # Fallback for different formats
            try:
                parsed_date = parser.parse(date_string, fuzzy=True)
                return parsed_date.replace(day=1).strftime('%Y-%m-%d')
            except Exception:
                return None


def extract_postcode(address_string: str) -> str:
    """
    Custom function to extract a postcode from an address string. Finds matching postcode strings, but returns the right-most match

    Args:
        address_string: An address string with a standard format UK postcode in it (eg. DL7 8AE)

    Returns:
        A string containing the post code only
    """
    # Replace O with 0 in strings that 'might' be a postcode
    address_string = re.sub(
        r' O([A-Z]{2})$', r' 0\1', address_string.upper().strip())

    # Use Regex to look for standard post code format in the string provided
    # pattern = r'([A-Z]{1,2}[0-9][A-Z0-9]? [0-9][A-Z]{2})'
    pattern = r'([A-Z]{1,2}[0-9][A-Z0-9]?\s+[0-9][A-Z]{2})'

    # Look for all matches in the address_string
    matches = re.findall(pattern, address_string)

    # Return the final match (right-most)
    if matches:
        return ' '.join(matches[-1].split())

    return None


def standardise_districts(df):
    """
    Function takes our business rates dataframe and looks to add in a fixed_district column. 
    This column looks at stamping each row of data with the latest 'district' based on the address postcode.
    If an exact match can't be found we start looking for the 'closest' postcode instead.

    Args:
        df: The dataframe we have created during step1

    Returns:
        A new dataframe with an additional column
    """

    # Sort data by address_postcode and snapshot_label_date
    df['snapshot_label_date'] = pd.to_datetime(df['snapshot_label_date'])
    df = df.sort_values(
        by=['address_postcode', 'snapshot_label_date'], ascending=[True, False])

    # Create list of 'approved' districts to use
    approved_districts = ['Craven', 'Hambleton', 'Harrogate',
                          'Richmondshire', 'Rydale', 'Scarborough', 'Selby']

    # Start building up mapping data
    mapping_df = df[df['District'].isin(
        approved_districts)].drop_duplicates('address_postcode')

    postcode_dict = {}
    for _, row in mapping_df.iterrows():
        pc = str(row['address_postcode']).strip().upper()
        dist = row['District']

        # Populate dictionary
        for i in range(len(pc), 2, -1):
            trunc_pc = pc[:i].strip()
            if trunc_pc not in postcode_dict:
                postcode_dict[trunc_pc] = dist

    # Start applying logic
    def find_closest_match(pc):
        if not pc or pd.isna(pc):
            return 'Unknown'

        target = str(pc).strip().upper()

        for i in range(len(target), 2, -1):
            attempt = target[:i].strip()
            if attempt in postcode_dict:
                return postcode_dict[attempt]

        return 'New/Unassigned'

    df['fixed_district'] = df['address_postcode'].apply(find_closest_match)

    return df


def calculate_rates(df):
    """
    Function that takes our ingested data df and applies the NYC business rates multipliers as below;
        2025/2026
        - 49.9p for rateable values of under £51,000
        - 55.5p for rateable values of £51,000 or higher

    Args:
        df: Our creared dataframe from business rate ingestion

    Returns:
        df: With additional columns based on the above logic
    """

    # Assign correct multiplier
    df['br_multiplier'] = np.where(
        df['Current Rateable Value'] < 51000, 0.499, 0.555)

    # Calculate gross br bill
    df['gross_br_bill'] = df['Current Rateable Value'] * df['br_multiplier']

    # Start to calculate net bill based on reliefs
    df['net_br_bill'] = df['gross_br_bill']

    # Small business rate relief of 100% (RV < £12,000)
    sb_mask = (df['Current Rateable Value'] < 12000)
    df.loc[sb_mask, 'net_br_bill'] = 0

    # Charity relief of 80% discount
    charity_mask = df['Current Relief 1'].str.contains(
        'charity', na=False, case=False)
    df.loc[charity_mask, 'net_br_bill'] = df['net_br_bill'] * 0.2

    # Empty property relief of 100% discount
    charity_mask = df['Current Relief 1'].str.contains(
        'empty', na=False, case=False)
    df.loc[charity_mask, 'net_br_bill'] = 0

    return df


def normalize_prop_id(ref):
    """
    Function to take both new and old style property id values from ingested data and normalize

    Args:
        ref: either old or new style prop id values

    """
    ref = str(ref).strip()

    # Handle newer 16 digit ID values (2 digit prefix, 11 digit core, 3 digit suffix)
    if len(ref) == 16:
        return ref[2:13]
    if ref.startswith('N'):
        return ref[1:12]
    return ref[:11]

    """
    # Handle older 12 digit ID values (1 letter prefix, 11 digit core)
    if len(ref) == 12:
        if ref[0].isalpha():
            return ref[1:12]
        # If all numbers return first 11 digits
        else:
            return ref[0:11]
 
    return ref
    """


def apply_prorata_logic(df):
    """
    """
    # Clean dates to be used
    df['snapshot_label_date'] = pd.to_datetime(df['snapshot_label_date'])
    df['Account Start date'] = pd.to_datetime(
        df['Account Start date'], errors='coerce')

    # Add in normalised property id
    df['normalised_prop_id'] = df['Property Reference Number'].apply(
        normalize_prop_id)

    # Add in occupant_id
    df['occupant_id'] = df['normalised_prop_id'].astype(
        str) + ' | ' + df['Primary Liable party name'].fillna('Unknown').astype(str)

    # Get list of snapshot dates in data
    snapshots = sorted(df['snapshot_label_date'].unique())
    periods = []

    for i, end_date in enumerate(snapshots):
        if i == 0:
            # First snapshot: look back 12 months from earliest data
            start_date = end_date - pd.DateOffset(years=1)
        else:
            # Each subsequent snapshot takes the start date from the end date of the previous one
            start_date = snapshots[i-1] + pd.Timedelta(days=1)

        periods.append({
            'snapshot_label_date': end_date,
            'period_start': start_date,
            'period_end': end_date
        })

    periods_df = pd.DataFrame(periods)
    df = df.merge(periods_df, on='snapshot_label_date', how='left')

    # Flag closures by looking ahead and comparing occupant_id values
    for i in range(len(snapshots) - 1):
        current_snap = snapshots[i]
        next_snap = snapshots[i + 1]

        current_ids = set(df[df['snapshot_label_date'] ==
                          current_snap]['occupant_id'])
        next_ids = set(df[df['snapshot_label_date']
                       == next_snap]['occupant_id'])

        dropped_ids = current_ids - next_ids

        # update status where dropped IDs are not in current snapshot
        df.loc[(df['snapshot_label_date'] == current_snap) &
               (df['occupant_id'].isin(dropped_ids)), 'lifecycle_status'] = 'Closed Business'

    """
    # Flag new and active statuses for remaining rows
    def get_status(row):
        # If already flagged as Closed, keep it
        if hasattr(row, 'lifecycle_status') and row['lifecycle_status'] == 'Closed Business':
                return 'Closed Business'
        if pd.notnull(row['Account Start date']):
            if row['period_start'] <= row['Account Start date'] <= row['period_end']:
                return 'New Opening'
        return 'Active'
    """

    # Flag and set other lifecycle_status values
    def get_status(row):
        # If already flagged as 'Closed Business' leave as this
        if pd.notnull(row['lifecycle_status']):
            return row['lifecycle_status']

        # Flag 'New Business' rows
        if pd.notnull(row['Account Start date']):
            if row['period_start'] <= row['Account Start date'] <= row['period_end']:
                return 'New Opening'

        return 'Active'

    # Apply status to remaining data
    df['lifecycle_status'] = df.apply(get_status, axis=1)

    # Start looking at prorata figures
    df['days_in_period'] = (df['period_end'] - df['period_start']).dt.days + 1

    def calculate_prorata(row):
        daily_rate = row['net_br_bill'] / 365.0
        if row['lifecycle_status'] == 'New Opening':
            days_active = (row['period_end'] -
                           row['Account Start date']).days + 1
            return daily_rate * max(days_active, 0)
        return daily_rate * row['days_in_period']

    df['prorata_net_bill'] = df.apply(calculate_prorata, axis=1)

    return df


def clean_business_categories(df):
    """
    Function to look at creating a unified single business/analytics description column. This also
    looks at fixing possible data issues for snapshots with missing descriptions and looks to create
    a handful of clean 'sectors' for aggregation.

    Args:
        df: Our ingested snapshot dataframe
    Returns:
        df: Updated dataframe with a 'business_category' and 'business_section' columns
    """
    # Combine 'Current Analysis Code Description' and 'Current VOA Description' columns
    df['business_category'] = df['Current Analysis Code Description'].combine_first(
        df['Current VOA Description'])

    # Backfill any blank 'business_category' values for businesses with the first value they have this populated
    cat_lookup = df[df['business_category'].notnull()].sort_values(
        'snapshot_label_date').groupby('occupant_id')['business_category'].first()
    # df['business_category'] = df['business_category'].fillna(df['occupant_id']).map(cat_lookup)
    df.loc[df['business_category'].isnull(
    ), 'business_category'] = df['occupant_id'].map(cat_lookup)

    # Standardise plurals and conjunctions
    df['business_category'] = (df['business_category']
                               .fillna('Uncategorised')
                               .str.replace(' And ', ' & ', case=False)
                               .str.replace('Offices', 'Office', case=False)
                               .str.replace('Car Parks', 'Car Park', case=False)
                               .str.strip())

    # Create mapping for higher level 'business_segment'
    def sector_map(val):
        v = val.lower()
        if v == 'uncategorisied':
            return 'Other'

        # Retail
        if any(x in v for x in ['shop', 'store', 'showroom', 'retail', 'post office', 'hairdressing', 'salon', 'market', 'pharmacy', 'kiosk', 'launderette', 'petrol']):
            return 'Retail'
        # Office
        if any(x in v for x in ['office', 'studio', 'surgery', 'clinic', 'bank', 'business center', 'health centre', 'surgery']):
            return 'Office'
        # Hospitality
        if any(x in v for x in ['pub', 'hotel', 'inn', 'restaurant', 'cafe', 'guest house', 'holiday', 'caravan', 'chalet', 'camping', 'boarding', 'wine bar']):
            return 'Hospitality'
        # Industrial
        if any(x in v for x in ['factory', 'factories', 'warehouse', 'workshop', 'industrial', 'depot', 'storage', 'garage', 'works', 'mill']):
            return 'Industrial'
        # Public & Utilities
        if any(x in v for x in ['sewage', 'communication', 'electricity', 'water', 'gas', 'mast', 'substation', 'school', 'college', 'education', 'church', 'library', 'police', 'fire', 'hospital', 'nursery', 'council', 'cemetery', 'crematoria']):
            return 'Public & Utilities'
        # Leisure
        if any(x in v for x in ['leisure', 'club', 'gym', 'cinema', 'theatre', 'sports', 'golf', 'museum', 'gallery', 'community centre', 'hall & premises']):
            return 'Leisure'

        return 'Other'

    df['business_sector'] = df['business_category'].apply(sector_map)

    return df
