import great_expectations as gx
import pandas as pd
import sys

def validate_data():
    print("Initializing Great Expectations context...")
    context = gx.get_context()

    # Define Data Source
    datasource_name = "my_filesystem_datasource"
    # Note: Simplification for portfolio script - treating dataframe as runtime asset or using pandas helper
    
    df = pd.read_csv('data/users.csv')
    print("Loaded data:")
    print(df)
    
    # Convert to GX Dataset (older API) or Validator (newer API)
    # Using 'from_dataset' for simplicity in scripts without full config setup
    batch_name = "users_batch"
    datasource = context.sources.add_pandas(datasource_name)
    asset = datasource.add_dataframe_asset(name=batch_name, dataframe=df)
    
    # Define Expectation Suite
    suite_name = "user_validation_suite"
    context.add_or_update_expectation_suite(expectation_suite_name=suite_name)
    
    # Build Batch Request
    batch_request = asset.build_batch_request()
    validator = context.get_validator(
        batch_request=batch_request,
        expectation_suite_name=suite_name
    )

    print("\nAdding Expectations...")
    
    # 1. ID must be unique
    validator.expect_column_values_to_be_unique(column="id")
    
    # 2. Name cannot be null
    validator.expect_column_values_to_not_be_null(column="name")
    
    # 3. Age must be between 18 and 100
    validator.expect_column_values_to_be_between(column="age", min_value=18, max_value=100)
    
    # 4. Email must match regex
    validator.expect_column_values_to_match_regex(column="email", regex=r"[^@]+@[^@]+\.[^@]+")

    # Validate
    print("\nRunning Validation...")
    results = validator.validate()
    
    # Output
    success = results["success"]
    print(f"Validation Success: {success}")
    
    if not success:
        print("\nFailures detected:")
        for res in results["results"]:
            if not res["success"]:
                print(f"- {res['expectation_config']['expectation_type']} failed on column {res['expectation_config']['kwargs'].get('column')}")
                print(f"  Unexpected count: {res['result']['unexpected_count']}")
                print(f"  Partial unexpected list: {res['result']['partial_unexpected_list']}")

    # Save to Docs (Optional demonstration)
    # context.build_data_docs()
    # context.open_data_docs()

if __name__ == "__main__":
    validate_data()
