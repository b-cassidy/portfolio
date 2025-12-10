import os
from datetime import datetime, timedelta
from typing import List, Optional

import numpy as np
import pandas as pd
from faker import Faker


class CreateTelephonyData:
    """
    Generates a sample telephony call data CSV file for portfolio use.

    The generator creates a DataFrame of simulated calls with realistic
    characteristics, including single and multi-call conversations, handling
    abandoned calls, and adjusting call times for concurrent calls.
    """

    # --- Configuration Constants (Class Attributes) ---
    EMPLOYEE_FILE: str = 'telephony_data/sample_employee.csv'
    OUTPUT_FILE: str = 'telephony_data/sample_telephony.csv'
    QUEUE_NAMES: List[str] = [
        'Customer Service', 'Sales', 'Renewals', 'Finance']

    def __init__(
        self,
        num_rows: int = 20000,
        start_date: datetime = datetime(2025, 1, 1),
        end_date: datetime = datetime(2025, 1, 31),
        fcr_rate: float = 0.95,
        abn_rate: float = 0.05,
        seed: int = 42
    ):
        """
        Initializes the data generator with specific configuration parameters.

        Args:
            num_rows: Total number of rows (calls) to generate.
            start_date: Start date for the call date range.
            end_date: End date for the call date range.
            fcr_rate: First Call Resolution rate (proportion of single-calls).
            abn_rate: Abandonment rate.
            seed: Seed for random number generation reproducibility.
        """
        print("Initializing CreateTelephonyData...")

        # --- Assign passed parameters to instance attributes (snake_case) ---
        self.num_rows = num_rows
        self.start_date = start_date
        self.end_date = end_date
        self.fcr_rate = fcr_rate
        self.abn_rate = abn_rate

        # --- Internal Setup ---
        # 1. Initialize Faker and seed it specifically
        self.fake = Faker('en_GB')
        self.fake.seed_instance(seed)

        # 2. Create a local RNG instance for Numpy (isolates randomness)
        self.rng = np.random.default_rng(seed)

        self.df: pd.DataFrame = pd.DataFrame()
        self.employee_ids: List[str] = []

        self._load_employee_data()

    def _load_employee_data(self):
        """Loads employee data, filters for latest records, and gets IDs."""
        if not os.path.exists(self.EMPLOYEE_FILE):
            raise FileNotFoundError(
                f"Employee file not found: {self.EMPLOYEE_FILE}")

        df_employee = pd.read_csv(self.EMPLOYEE_FILE, header=0)

        df_employee['latest_row'] = (
            df_employee.groupby('EmployeeID')['Updated']
            .rank(method='dense', ascending=False)
        )
        df_employee = df_employee[df_employee['latest_row'] == 1.0].copy()
        self.employee_ids = df_employee['EmployeeID'].tolist()
        print(f"Loaded {len(self.employee_ids)} unique employee IDs.")

    def _generate_conversation_ids(self):
        """Generates ConversationID values based on fcr_rate."""
        num_single_call = int(self.num_rows * self.fcr_rate)
        num_remaining = self.num_rows - num_single_call
        num_multi_call_conv = num_remaining // 2

        single_call_ids = [self.fake.uuid4() for _ in range(num_single_call)]
        multi_call_ids = [self.fake.uuid4()
                          for _ in range(num_multi_call_conv)] * 2

        all_ids = single_call_ids + multi_call_ids
        self.df['ConversationID'] = all_ids[:self.num_rows]

    def _generate_dates_and_times(self):
        """Generates random CallDate and CallTime."""
        date_range_days = (self.end_date - self.start_date).days

        # use self.rng instead of np.random
        random_days = self.rng.integers(0, date_range_days + 1, self.num_rows)

        call_dates = [
            self.start_date.date() + timedelta(days=int(d)) for d in random_days
        ]
        self.df['CallDate'] = call_dates

        time_objects = [self.fake.time_object() for _ in range(self.num_rows)]

        self.df['CallTime'] = [
            datetime.combine(d, t) for d, t in zip(call_dates, time_objects)
        ]

    def _generate_queue_and_status(self):
        """Generates QueueName, TimeInQueue, and CallStatus."""
        # use self.rng
        self.df['QueueName'] = self.rng.choice(self.QUEUE_NAMES, self.num_rows)
        self.df['TimeInQueue'] = self.rng.integers(0, 601, self.num_rows)

        answered_mask = self.rng.choice(
            [True, False],
            size=self.num_rows,
            p=[1 - self.abn_rate, self.abn_rate]
        )
        self.df['CallStatus'] = np.where(
            answered_mask, 'Answered', 'Abandoned')
        self.df['answered_mask'] = answered_mask

    def _generate_call_metrics(self):
        """Generates HandleTime, TalkTime, etc. only for answered calls."""
        df_answered = self.df[self.df['answered_mask']].copy()
        df_abandoned = self.df[~self.df['answered_mask']].copy()

        n_ans = len(df_answered)

        # use self.rng
        df_answered['HandledBy'] = self.rng.choice(self.employee_ids, n_ans)
        df_answered['TalkTime'] = self.rng.integers(30, 3000, n_ans)
        df_answered['HoldTime'] = self.rng.integers(0, 500, n_ans)
        df_answered['WrapTime'] = self.rng.integers(5, 2000, n_ans)

        df_answered['HandleTime'] = (
            df_answered['TalkTime'] +
            df_answered['HoldTime'] +
            df_answered['WrapTime']
        )

        df_abandoned['HandledBy'] = 'N/A'
        df_abandoned['TalkTime'] = 0
        df_abandoned['HoldTime'] = 0
        df_abandoned['WrapTime'] = 0
        df_abandoned['HandleTime'] = 0

        self.df = pd.concat([df_answered, df_abandoned]).sort_index()
        self.df.drop(columns=['answered_mask'], inplace=True)

        self.df = self.df.sort_values(
            by=['ConversationID', 'CallTime'], ascending=[True, True]
        ).reset_index(drop=True)

    @staticmethod
    def _adjust_times_group(group: pd.DataFrame) -> pd.DataFrame:
        """Adjusts the CallTime for concurrent calls within a group."""
        if len(group) <= 1:
            return group

        # Iterate through the group starting from the second item
        for i in range(1, len(group)):
            prev_call_start = group.iloc[i-1]['CallTime']
            prev_call_queue = group.iloc[i-1]['TimeInQueue']
            prev_call_handle = group.iloc[i-1]['HandleTime']

            time_to_add = (
                pd.Timedelta(seconds=prev_call_queue) +
                pd.Timedelta(seconds=prev_call_handle)
            )
            new_call_start = prev_call_start + time_to_add

            group.loc[group.index[i], 'CallTime'] = new_call_start

        return group

    def _adjust_concurrent_call_times(self):
        """Applies the time adjustment function across all conversations."""
        print("Adjusting call times for multi-call conversations...")

        self.df = self.df.groupby(
            'ConversationID', group_keys=False
        ).apply(self._adjust_times_group)

        # Fix datetime format after adjustments
        self.df['CallTime'] = pd.to_datetime(self.df['CallTime'])
        self.df['CallDate'] = self.df['CallTime'].dt.date
        self.df['CallTime'] = self.df['CallTime'].dt.time

    def generate_data(self) -> pd.DataFrame:
        """Executes the entire data generation pipeline."""
        print(f"Starting data generation for {self.num_rows} rows...")
        print(f"Calls run from {self.start_date} to {self.end_date}")
        print(f"FCR Rate: {self.fcr_rate}, Abn Rate: {self.abn_rate}")

        self._generate_conversation_ids()
        self._generate_dates_and_times()
        self._generate_queue_and_status()
        self._generate_call_metrics()
        self._adjust_concurrent_call_times()

        print("Data generation complete.")
        return self.df

    def save_to_csv(self, df: Optional[pd.DataFrame] = None):
        """Saves the generated DataFrame to the configured output file."""
        df_to_save = df if df is not None else self.df
        os.makedirs(os.path.dirname(self.OUTPUT_FILE), exist_ok=True)
        df_to_save.to_csv(self.OUTPUT_FILE, index=False)
        print(
            f"\n✅ Successfully created '{self.OUTPUT_FILE}' "
            f"with {len(df_to_save)} rows of telephony data."
        )


if __name__ == '__main__':
    # --- Example Usage ---
    try:
        # Default initialization (uses internal default seed=42)
        generator = CreateTelephonyData()

        # Example of custom run
        # generator = TelephonyDataGenerator(
        #     num_rows=100000,
        #     start_date=datetime(2025, 12, 1),
        #     end_date=datetime(2025, 12, 31),
        #     fcr_rate=0.75,
        #     abn_rate=0.00
        # )

        df_result = generator.generate_data()
        generator.save_to_csv(df_result)

    except FileNotFoundError as e:
        print(f"\n❌ ERROR: {e}")
        print("Please ensure the employee CSV file exists.")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")
