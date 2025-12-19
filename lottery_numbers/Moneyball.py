"""
Below will look at creating a new class called 'Moneyball' which will;
    1. Scrape the national lottery results webpage for the past 180 days of results
    2. Process this data to return;
        a - The most common 6 numbers to appear in drawers
        b - Hihglight from these potetnial jackpots if these 6 numbers were played as well as the amount
            of 'winning' drawers these numbers would have matched on 
        c - Highlight the most common 'winning' numbers (ranging from 3 to 6 matching numbers in drawers)
    3. Take an input of 6 numbers to show along with the values from 2 what potential winnings would have 
        been from 6 numbers picked and also the number of 'winning' matches from the six numbers selected
"""

# Import libraries
import requests
import pandas as pd
from io import StringIO


url = 'https://www.national-lottery.co.uk/results/lotto/draw-history/csv'
old_results = 'lottery_numbers/lotto_results.csv'

###########################################################


def refresh_data(url, old_results):
    """
    First part of this refreshes the lotto draw data, by first checking if old_results are available.
    If they are, load new results from url and merge the two, if not then load new results from url only.
    """

    old_count = 0
    results_count = 0
    # First get the new lotto results if they are available from the url provided
    try:
        respone = requests.get(url)
        respone.raise_for_status()

        new_df = pd.read_csv(StringIO(respone.text), skiprows=0)
        print('Downloaded fresh data from Lotto csv file')

    # If url not available, display error and exit
    except requests.exceptions.RequestException as e:
        print(f"Error fetching CSV data: {e}")
        exit()

    # Then grab the old data from any existing csv file
    try:
        with open(old_results, 'r') as file:
            old_df = pd.read_csv(old_results, header=0)
            old_count = len(old_df)
            print(
                f'Old data exists, holding {old_count} rows. Appending new data to this...')

            # Combine old_results and new_results and remove duplicates
            results = pd.concat([new_df, old_df])
            results = results.drop_duplicates()

    # Exception triggered if old file does not exist
    except:
        print('Old data not found, loading new data only...')
        results = new_df

    # Write out data to csv
    results_count = len(results)
    results_count = results_count - old_count
    results.to_csv(old_results, index=False)
    print(f'Lotto results have been updated ({results_count} rows added) ✅')

    return results


###########################################################
def find_top_numbers(df: pd.DataFrame):
    """
    Function to find the most commonly drawn six numbers from the lotto drawers.
    This is excluding the bonus ball number.
    """


###########################################################
def top_bonus_balls(df: pd.DataFrame):
    """
    Function to find the most commonly drawn six bonus ball numbers from the lotto draws
    """


###########################################################
def top_combinations(df: pd.DataFrame):
    """
    This function will look at the past lotto results and find the most common combinations of drawn numbers.
    """


###########################################################
def prize_breakdown(df: pd.DataFrame, nums: set = find_top_numbers):
    """
    Function to estimate potetnial winnings by playing a set of 6 numbers.
    If no set is provided will use the results from find_top_numbers by default.
    """


###############################################################################################################################
########################################################### TESTING ###########################################################
###############################################################################################################################

# refresh_data(url, old_results)
"""
Below code loads the lotto_results.csv and begins to look at analysing the results
"""

# Load specific data from old_results file
cols = ['Ball 1', 'Ball 2', 'Ball 3', 'Ball 4', 'Ball 5', 'Ball 6']
results_df = refresh_data(url, old_results)[cols]
draw_count = len(results_df)

# Convert draw results into single series to get most commonly drawn balls
results_series = results_df.stack()
drawn_count = results_series.value_counts()
top_numbers = sorted(drawn_count.head(6).index.to_list())

# Once you have the most commonly drawn numbers, start looking at how often you could 'win' with these numbers

# Initialise matched number counters
match_counts = {
    '6 numbers matched': 0, '5 Numbers matched': 0, '4 Numbers matched': 0, '3 Numbers matched': 0
}

# Start to loop through main draw numbers for matches
for index, row in results_df.iterrows():
    draw_numbers = set(row[cols].to_list())

    # Intersection will compare the drawn numbers to our top numbers and start to count the matches
    matches = draw_numbers.intersection(top_numbers)
    num_matches = len(matches)

    # Count the number of draws where we match 3, 4, 5 or 6 numbers
    if num_matches == 6:
        match_counts['6 numbers matched'] += 1
    elif num_matches == 5:
        match_counts['5 Numbers matched'] += 1
    elif num_matches == 4:
        match_counts['4 Numbers matched'] += 1
    elif num_matches == 3:
        match_counts['3 Numbers matched'] += 1

# Show potential winnings from number matches based on 'average' prizes for 3, 4, 5 & 6 numbers matching
estimated_returns = {}
total_winnings = 0

# Create second dictionary of estimated winnings based on number matches
avg_prizes = {
    '6 Numbers matched': 3000000, '5 Numbers matched': 1750, '4 Numbers matched': 140, '3 Numbers matched': 30
}

# Start matching match_counts to _avg_prizes
for match_tier, draws_count in match_counts.items():

    # Get the avg_prize value and match to match_count
    prize_value = avg_prizes.get(match_tier, 0)

    # Calculate tier winnings
    tier_winnings = draws_count * prize_value

    # Store results as we iterate
    estimated_returns[tier_winnings] = tier_winnings

    # Add to grand totals
    total_winnings += tier_winnings

# Populate estimated_returns
estimated_returns['TOTAL winnings'] = total_winnings


# Start to show results
print(
    f'The most commonly drawn numbers from {draw_count} draws are {top_numbers}')
print(match_counts)
