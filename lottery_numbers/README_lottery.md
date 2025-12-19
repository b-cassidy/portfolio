💰 Moneyball: National Lottery Analysis & SQL Combinatorics
A dual-approach data engineering project that analyzes UK National Lottery historical data. This project demonstrates ETL pipelining in Python and advanced relational logic in SQL to identify statistical trends and frequent number sequences.

🚀 Project Overview
The project is split into two specialized modules:

Moneyball.py: Handles Data Acquisition (Scraping), Persistence (CSV handling), and Strategy Backtesting.

Moneyball_sql.py: Solves the "Combination Explosion" problem using SQL CTEs and Self-Joins to find the most frequent triplets of numbers.

🛠️ Technical Deep Dive
1. Data Engineering (Python)

The Python module focuses on a robust ETL (Extract, Transform, Load) process:

Intelligent Updates: Instead of re-downloading the entire history, the script merges new web-scraped data with existing local CSVs and handles de-duplication.

Backtesting Engine: Calculates historical ROI by simulating a "Most Frequent Numbers" strategy against years of draw data.

2. Relational Analytics (SQL)

To find the most common three-number sequences, the project utilizes pandasql to run complex queries against DataFrames.

The Challenge: A single lottery draw of 6 numbers contains 20 possible 3-number combinations. Finding these across thousands of draws is computationally expensive. The Solution: * Normalization: I used a UNION ALL inside a Common Table Expression (CTE) to pivot "Wide" data into a "Long" format.

Inequality Joins: I implemented A.Num < B.Num < C.Num logic. This ensures that the sequence (1, 2, 3) is only counted once, preventing the query from treating (3, 2, 1) or (2, 1, 3) as different sets.

SQL
-- Demonstrating the Inequality Join for unique combinations
SELECT A.Num, B.Num, C.Num, COUNT(*)
FROM LongLotto A
JOIN LongLotto B ON A.DrawNumber = B.DrawNumber AND A.Num < B.Num
JOIN LongLotto C ON B.DrawNumber = C.DrawNumber AND B.Num < C.Num
...
📊 Key Results & Insights
Frequency Analysis: Identifies "Hot" vs "Cold" numbers over a rolling 180-day window.

Triplet Discovery: Reveals which sets of three numbers appear together most often—a task that would be significantly more complex to write in pure Python.

Financial Backtesting: Quantifies the "Gambler's Fallacy" by showing the actual theoretical winnings of frequency-based play.

📋 How to Run
Clone the Repo:

Bash
git clone https://github.com/b-cassidy/portfolio
Install Requirements:

Bash
pip install pandas pandasql requests
Run Analysis:

python Moneyball.py (For latest data and backtesting)

python Moneyball_sql.py (For sequence analysis)

Why this belongs in my portfolio:

Demonstrates SQL Proficiency: Shows I can write complex joins and CTEs beyond simple SELECT * statements.

Data Integrity: Shows I understand how to manage local datasets and prevent data duplication.

Efficiency: Shows I can choose between Python sets for speed and SQL joins for complex relationships.