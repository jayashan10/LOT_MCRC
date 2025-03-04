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
    # input_df = pd.read_csv('data/input_data.csv', parse_dates=['administratedate']) # Important: parse dates
    input_df = pd.read_csv('data/input_data_syn.csv', parse_dates=['administratedate']) # Important: parse dates
    print(input_df.dtypes) # Print data types of the DataFrame
    print(input_df['administratedate'].head()) # Print the first few dates to inspect format

    # --- 3. Define Lines of Therapy for CRC ---
    detailed_output, summary_output, = define_treatment_lines_oncology(
        input_df.copy(),
        gap_period_options,
        new_biologic_agent_options,
        new_chemo_agent_options,
        drug_interchangeability_rules
    )

    # --- 4. Save Outputs to CSV ---
    detailed_output.to_csv('output/crc_lot_detailed.csv', index=False)
    summary_output.to_csv('output/crc_lot_summary.csv', index=False)

    print("CRC Line of Therapy definition completed.")
    print("Detailed output saved to output/crc_lot_detailed.csv")
    print("Summary output saved to output/crc_lot_summary.csv")

    # Optional: Display summary statistics
    print("\nSummary of Lines of Therapy:")
    print(summary_output.groupby('patientid')['line_of_therapy'].max().describe())

    # Example usage
    # def main():
    #     # Your existing code to process the data
    #     detailed_output, summary_output, timeline_viewer = define_treatment_lines_oncology(
    #         df, gap_period_options, new_biologic_agent_options, 
    #         new_chemo_agent_options, drug_interchangeability
    #     )
        
    #     # View timeline for a specific patient
    #     patient_id = "12345"  # Replace with actual patient ID
    #     timeline_file = timeline_viewer.view_patient_timeline(patient_id)
        
    #     # The timeline will be saved as an HTML file that you can open in a browser
    #     # It will show:
    #     # 1. Interactive timeline with drug administrations by line
    #     # 2. Drug exposure pattern
    #     # 3. Hover information for details
    #     # 4. Ability to zoom and pan
    #     # 5. Export options for the visualization