from lot_definition import define_treatment_lines_oncology  # Import the function
import pandas as pd
import yaml # or import json if using JSON config

# ... (your _colorectal_lot function and define_treatment_lines_oncology function from above) ...

if __name__ == '__main__':
    # --- 1. Load Configuration from YAML file ---
    with open('data/config.yaml', 'r') as file:
        config = yaml.safe_load(file)

    cancer_type = config['cancer_type']
    gap_period_options = config['gap_period_options']
    new_biologic_agent_options = config['new_biologic_agent_options']
    new_chemo_agent_options = config['new_chemo_agent_options']
    drug_interchangeability_rules = config['drug_interchangeability_rules']


    # --- 2. Load Input Data from CSV file ---
    input_df = pd.read_csv('data/input_data.csv')
    input_df['administratedate'] = pd.to_datetime(input_df['administratedate'])

    # Sort data
    input_df = input_df.sort_values(['patientid', 'administratedate'])
    print(input_df.dtypes) # Print data types of the DataFrame
    print(input_df['administratedate'].head()) # Print the first few dates to inspect format

    # --- 3. Define Lines of Therapy for CRC ---
    crc_df_with_lot = define_treatment_lines_oncology(
        input_df.copy(), # Use .copy() to avoid modifying original input_df
        gap_period_options,
        new_biologic_agent_options,
        new_chemo_agent_options,
        # maintenance_gap_options={}, # Not used for CRC, pass empty dict
        drug_interchangeability_rules
    )

    # --- 4. Save Output to CSV ---
    crc_df_with_lot.to_csv('output/crc_lot_output.csv', index=False)

    print("CRC Line of Therapy definition completed. Output saved to output/crc_lot_output.csv")