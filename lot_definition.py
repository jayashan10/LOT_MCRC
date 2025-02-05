import pandas as pd

def define_treatment_lines_oncology(df, gap_period_options, new_biologic_agent_options, new_chemo_agent_options, drug_interchangeability):
    """
    Defines lines of therapy for oncology patients using real-world data (CRC - Corrected Patient Handling).

    Args:
        df (pd.DataFrame): Input DataFrame (same columns as before).
        cancer_type (str): 'CRC'
        gap_period_options (dict): Gap period options (same as before).
        new_biologic_agent_options (dict): New biologic agent options (same as before).
        new_chemo_agent_options (dict): New chemo agent options (same as before).
        drug_interchangeability (dict): Drug interchangeability rules (same as before).

    Returns:
        pd.DataFrame: DataFrame with added 'line_of_therapy', 'regimen', 'line_start_date', 'line_end_date' columns.
    """

    df = df.sort_values(by=['patientid', 'administratedate'])
    
    # Initialize columns
    df['line_of_therapy'] = 0
    df['regimen'] = ''
    df['line_start_date'] = None
    df['line_end_date'] = None

    current_patient_id = None
    line_counter = 0
    current_regimen_drugs = set()
    last_admin_date = None
    last_line_start_date = None
    current_regimen = ''

    for index, row in df.iterrows():
        patient_id = row['patientid']
        drug_name = row['drugname']
        admin_date = row['administratedate']
        drug_category = row['drugcategory']

        # Reset for new patient
        if patient_id != current_patient_id:
            line_counter = 1
            current_regimen_drugs = set([drug_name])
            current_regimen = drug_name
            last_admin_date = admin_date
            last_line_start_date = admin_date
            current_patient_id = patient_id
            
            df.at[index, 'line_of_therapy'] = line_counter
            df.at[index, 'regimen'] = current_regimen
            df.at[index, 'line_start_date'] = admin_date
            df.at[index, 'line_end_date'] = admin_date
            continue

        # Check for line change conditions
        new_line_needed = False
        
        # 1. Treatment Gap Rule
        if last_admin_date and (admin_date - last_admin_date).days > gap_period_options['gap_treatment_restart']:
            new_line_needed = True
            
        # 2. Biologic Addition Rule (non-EGFR)
        elif drug_category in ('biologics', 'targeted') and drug_name not in drug_interchangeability['CRC']['anti_egfr']:
            if last_line_start_date and (admin_date - last_line_start_date).days > new_biologic_agent_options['after_initial_period']:
                new_line_needed = True
                
        # 3. EGFR Inhibitor Rules
        elif drug_name in drug_interchangeability['CRC']['anti_egfr']:
            if last_line_start_date and (admin_date - last_line_start_date).days > new_biologic_agent_options['bio_dis1_period']:
                new_line_needed = True
                
        # 4. New Chemo Addition Rule
        elif drug_category == 'chemotherapy':
            is_fluoropyrimidine = drug_name in drug_interchangeability['CRC']['fluoropyrimidines']
            has_flu_in_regimen = any(drug in drug_interchangeability['CRC']['fluoropyrimidines'] 
                                   for drug in current_regimen_drugs)
            
            if not is_fluoropyrimidine and has_flu_in_regimen:
                if last_line_start_date and (admin_date - last_line_start_date).days > new_chemo_agent_options['flu_dis_period']:
                    new_line_needed = True

        # Start new line if needed
        if new_line_needed:
            line_counter += 1
            current_regimen_drugs = set([drug_name])
            current_regimen = drug_name
            last_line_start_date = admin_date
        else:
            # Update current regimen
            if drug_name not in current_regimen_drugs:
                current_regimen_drugs.add(drug_name)
                current_regimen = '+'.join(sorted(current_regimen_drugs))

        # Update row values
        df.at[index, 'line_of_therapy'] = line_counter
        df.at[index, 'regimen'] = current_regimen
        df.at[index, 'line_start_date'] = last_line_start_date
        df.at[index, 'line_end_date'] = admin_date
        
        last_admin_date = admin_date

    return df