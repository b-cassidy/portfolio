## 📞 Create Sample Telephony Data

This Python project contains the `CreateTelephonyData` class, designed to create large, realistic sample datasets of call center activity. This generated data is ideal for use in **data analysis projects, dashboard visualizations (e.g., Tableau, Power BI),** and **machine learning model training**, particularly for metrics related to call volume, agent performance, and customer experience.

### Key Features

  * **Scalable:** Generates up to millions of call records.
  * **Reproducible:** Uses specific random seeds for consistent output data (important for testing).
  * **Conversation Logic:** Simulates **First Call Resolution (FCR)** and multi-call conversations, ensuring chronological accuracy between linked calls.
  * **Metrics:** Calculates core telephony metrics like **Handle Time**, **Talk Time**, **Time in Queue**, and tracks **Abandoned** calls.

### ⚙️ Installation

1.  **Clone the repository** (or save the Python file) and navigate to the project directory.

2.  Install the necessary dependencies using `pip`:

    ```bash
    pip install pandas numpy faker
    ```

### 🚀 Usage

The script is configured to run directly from the command line using default values, but it can be easily customized.

#### 1\. Pre-Requisite (Employee Data)

This script requires a file named `telephony_data/sample_employee.csv` to exist. This file serves as a lookup list for agent IDs to be assigned to answered calls. A minimal version should contain at least two columns: `EmployeeID` and `Updated` (a date column).

#### 2\. Running with Default Configuration

Execute the script directly. It will generate **20,000 rows** of data for January 2025 using a 95% FCR rate and 5% Abandonment rate.

```bash
python telephony_data\create_telephony_data.py
```

*Output file:* `telephony_data/sample_telephony.csv`

#### 3\. Running with Custom Parameters

You can modify the `if __name__ == '__main__':` block in the Python file to use custom parameters.

```python
if __name__ == '__main__':
    try:
        # Example of a custom run:
        generator = CreateTelephonyData(
            num_rows=100000, 
            start_date=datetime(2025, 12, 1), 
            end_date=datetime(2025, 12, 31), 
            fcr_rate=0.75,         # 75% of calls are single-contact resolution
            abn_rate=0.00,         # 0% abandoned calls
            seed=100               # Custom seed for reproducibility
        )
        df_result = generator.generate_data()
        generator.save_to_csv(df_result)
        
    except FileNotFoundError as e:
        # ... error handling ...
```

-----

### 🔬 Testing (For Developers)

This project includes unit tests using `pytest` to ensure data adherence to the specified rates and logic.

1.  Install `pytest`:
    ```bash
    pip install pytest
    ```
2.  Run the tests (assuming your test file is named `test_telephony_data.py`):
    ```bash
    pytest telephony_data\test_telephony_data.py
    ```

The tests verify that the actual proportion of calls flagged as **Abandoned** and the actual count of **First Contact Resolution** rows closely match the input rates (`abn_rate` and `fcr_rate`) within a small statistical tolerance.

### 🧠  What next?

 1. Need to create separate python script to query new data, including some visuals using Matplotlib
 2. Another script to create aggregated data model CSV file that can be used in PBI
 3. Take new data file, import into PBI, build report and include here