# Automated Data Quality with Great Expectations

This project validates a sample dataset against a strict schema using the [Great Expectations](https://greatexpectations.io/) Python library. It demonstrates how to catch "dirty data" before it enters a production pipeline.

## Scenario
We have a `users.csv` file that supposedly comes from an upstream API. However, it contains several issues:
- Duplicated IDs
- Missing Names
- Invalid Ages (e.g., 150)
- Malformed Emails

## Setup & Run
1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Validation**:
   ```bash
   python validate_data.py
   ```

## Expected Output
The script will load the data, define Expectations, and fail with specific details:
- `expect_column_values_to_be_unique` failed on `id` (Count: 2)
- `expect_column_values_to_not_be_null` failed on `name` (Count: 1)
- `expect_column_values_to_be_between` failed on `age` (Count: 1)
- `expect_column_values_to_match_regex` failed on `email` (Count: 1)

## Key Concepts
- **Expectation Suite**: A collection of rules (tests) for your data.
- **Validators**: Objects that check a Batch of data against a Suite.
- **Data Docs**: Auto-generated HTML reports (commented out in script, but a key feature of GX).
