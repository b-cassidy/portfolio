"""
Using the lotto_results.csv file, the below code will look to ingest the data into a
pandas DataFrame and perform SQL operations on it to find us the most commonly drawn
three number sequence."""

import pandas as pd
import pandasql as ps
from pandasql import sqldf

# File path to lotto results
LOTTO_FILE = 'lottery_numbers/lotto_results.csv'

# Import lotto results data into DataFrame
lotto_df = pd.read_csv(LOTTO_FILE)

# print(lotto_df.head())

# Start to sort the data into three number sequences
query_1 = """
    -- Create long table of numbers drawn
    WITH LongLotto As (
        SELECT [DrawNumber], [Ball 1] As Num FROM lotto_df
        UNION ALL SELECT [DrawNumber], [Ball 2] FROM lotto_df 
        UNION ALL SELECT [DrawNumber], [Ball 3] FROM lotto_df
        UNION ALL SELECT [DrawNumber], [Ball 4] FROM lotto_df
        UNION ALL SELECT [DrawNumber], [Ball 5] FROM lotto_df
        UNION ALL SELECT [DrawNumber], [Ball 6] FROM lotto_df
    )
    
    -- Join long table to itself to find sequences of three numbers
    -- and limit results to top 10 most common
    SELECT
        A.Num As Num1,
        B.Num As Num2,
        C.Num As Num3,
        COUNT(*) As Frequency
    FROM LongLotto As A
    JOIN LongLotto As B
        ON A.[DrawNumber] = B.[DrawNumber] AND A.Num < B.Num
    JOIN LongLotto As C
        ON B.[DrawNumber] = C.[DrawNumber] AND B.Num < C.Num
    GROUP BY 
        A.Num
        , B.Num
        , C.Num
    ORDER BY 
        Frequency DESC
    LIMIT 10
    """

# Execute SQL query and store as DataFrame
sql_df = ps.sqldf(query_1, locals())

# Display results
print(sql_df.head(10))
