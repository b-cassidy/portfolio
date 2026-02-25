# Import libraries
import re
import pandas as pd


def extract_max_year(age_string):
    """
    Extract the maximum year from a construction age band string.

    Parameters:
    age_string (str): The construction age band string (e.g., '1900-1929', 'before 1900', '2000 onwards').

    Returns:
    int: The maximum year extracted from the age band, or None if it cannot be determined.
    """
    if pd.isna(age_string):
        return None
    # Find all 4 digit numbers in the string
    years = re.findall(r'\d{4}', age_string)
    if years:
        # If found, return the maximum year as an integer
        # return int(max(years))
        return max(map(int, years))
    return None


def assign_age_risk(year, rules):
    """
    Assign a risk score based on the construction age band year and predefined rules.

    Parameters:
    year (int): The construction year.
    rules (list of dict): The predefined rules for assigning risk scores.

    Returns:
    int: The assigned risk score.
    """
    if year is None:
        return 0  # Assign a default score for missing values
    # Loop through rules and assign score based on the maximum year
    for rule in rules:
        if year <= rule['year_max']:
            return rule['score']
    return 0  # Default score if no rules match


def assign_keyword_risk(description, rules):
    """
    Assign a risk score based on the presence of specific keywords in a description.

    Parameters:
    description (str): The text description to analyze. 
    rules (list of dict): A list of dictionaries where each dictionary contains a 'keyword' and a corresponding 'score'.

    Returns:
    int: The total risk score calculated based on the presence of keywords in the description.
    """
    if pd.isna(description):
        return 0  # Assign a default score for missing values
    # Convert to lowercase for case-insensitive matching
    description = description.lower()
    score = 0
    for rule in rules:
        if rule['keyword'] in description:
            score += rule['score']
    return score


def assign_imd_risk(decile, rules):
    """
    Assign a risk score based on IMD decile and predefined rules.

    Parameters:
    decile (int): The IMD decile value.
    rules (list of dict): A list of dictionaries where each dictionary contains a 'decile_max' and a corresponding 'score'.

    Returns:
    int: The assigned risk score based on the IMD decile.
    """
    if pd.isna(decile):
        return 0  # Assign a default score for missing values
    for rule in rules:
        if decile <= rule['decile_max']:
            return rule['score']
    return 0  # Default score if no rules match
