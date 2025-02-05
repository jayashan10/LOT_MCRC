import pandas as pd

def calculate_patient_lot(patient_df, gap_period_options, new_biologic_agent_options, new_chemo_agent_options, drug_interchangeability):
    """
    Calculate lines of therapy for a single patient incorporating both 28-day window
    and CRC-specific rules with enhanced drug handling.
    """
    # Initialize patient's first treatment
    line_counter = 1
    current_regimen_drugs = set([patient_df.iloc[0]['drugname']])
    last_admin_date = patient_df.iloc[0]['administratedate']
    last_line_start_date = last_admin_date
    current_regimen = patient_df.iloc[0]['drugname']
    is_initial_regimen = True
    
    # Track molecular markers and current regimen type
    current_regimen_type = None  # To track if it's FOLFOX, FOLFIRI, etc.
    has_anti_vegf = False
    has_anti_egfr = False
    
    # Initialize output columns
    patient_df = patient_df.copy()
    patient_df['line_of_therapy'] = 0
    patient_df['regimen'] = ''
    patient_df['line_start_date'] = None
    patient_df['line_end_date'] = None
    patient_df['regimen_status'] = ''
    patient_df['regimen_type'] = ''  # New column to track standard regimen types
    patient_df['maintenance_flag'] = False  # New column to identify maintenance therapy
    
    # Set first administration
    patient_df.iloc[0, patient_df.columns.get_loc('line_of_therapy')] = line_counter
    patient_df.iloc[0, patient_df.columns.get_loc('regimen')] = current_regimen
    patient_df.iloc[0, patient_df.columns.get_loc('line_start_date')] = last_line_start_date
    patient_df.iloc[0, patient_df.columns.get_loc('line_end_date')] = last_admin_date
    patient_df.iloc[0, patient_df.columns.get_loc('regimen_status')] = 'Initial Drug'
    
    def identify_standard_regimen(drugs):
        """Helper function to identify standard regimens"""
        drug_set = set(drugs)
        for regimen, components in drug_interchangeability['CRC']['standard_regimens'].items():
            if set(components).issubset(drug_set):
                return regimen
        return None
    
    def is_maintenance_therapy(drugs):
        """Helper function to identify maintenance therapy"""
        drug_set = set(drugs)
        for maintenance in drug_interchangeability['CRC']['sequence_rules']['maintenance_options']:
            maint_drugs = set(maintenance.split('+'))
            if maint_drugs.issubset(drug_set):
                return True
        return False
    
    # Process subsequent administrations
    for index, row in patient_df.iloc[1:].iterrows():
        drug_name = row['drugname']
        admin_date = row['administratedate']
        drug_category = row['drugcategory']
        
        days_since_line_start = (admin_date - last_line_start_date).days
        days_since_last_admin = (admin_date - last_admin_date).days
        
        new_line_needed = False
        regimen_status = ''
        
        # Phase 1: Initial Regimen Building (28-day window)
        if is_initial_regimen and days_since_line_start <= 28:
            if drug_name not in current_regimen_drugs:
                current_regimen_drugs.add(drug_name)
                current_regimen = '+'.join(sorted(current_regimen_drugs))
                regimen_status = 'Initial Combination'
                
                # Check if it forms a standard regimen
                current_regimen_type = identify_standard_regimen(current_regimen_drugs)
                if current_regimen_type:
                    regimen_status = f'Initial {current_regimen_type}'
            else:
                regimen_status = 'Continuation'
                
        # Phase 2: Post-Initial Regimen Rules
        else:
            is_initial_regimen = False
            
            # 1. Treatment Gap Rule
            if days_since_last_admin > gap_period_options['gap_treatment_restart']:
                new_line_needed = True
                regimen_status = 'New Line (Gap)'
                
            # 2. Biologic Rules (Enhanced)
            elif drug_category in ('biologics', 'targeted'):
                if drug_name in drug_interchangeability['CRC']['anti_vegf']:
                    if days_since_line_start > new_biologic_agent_options['after_initial_period']:
                        new_line_needed = True
                        regimen_status = 'New Line (Anti-VEGF Addition)'
                    else:
                        regimen_status = 'Anti-VEGF Addition (Within Window)'
                        has_anti_vegf = True
                        
                elif drug_name in drug_interchangeability['CRC']['anti_egfr']:
                    if days_since_line_start > new_biologic_agent_options['bio_dis1_period']:
                        new_line_needed = True
                        regimen_status = 'New Line (EGFR Addition/Switch)'
                    else:
                        regimen_status = 'EGFR Addition (Within Window)'
                        has_anti_egfr = True
                        
                elif drug_name in drug_interchangeability['CRC']['other_targeted']:
                    new_line_needed = True
                    regimen_status = 'New Line (Other Targeted Agent)'
                    
            # 3. Chemotherapy Rules (Enhanced)
            elif drug_category == 'chemotherapy':
                is_fluoropyrimidine = drug_name in drug_interchangeability['CRC']['fluoropyrimidines']
                has_flu_in_regimen = any(drug in drug_interchangeability['CRC']['fluoropyrimidines'] 
                                       for drug in current_regimen_drugs)
                
                # Handle platinum agents
                if drug_name in drug_interchangeability['CRC']['chemotherapy']['platinum']:
                    if has_flu_in_regimen and days_since_line_start > new_chemo_agent_options['flu_dis_period']:
                        new_line_needed = True
                        regimen_status = 'New Line (Platinum Addition)'
                        
                # Handle topoisomerase inhibitors
                elif drug_name in drug_interchangeability['CRC']['chemotherapy']['topoisomerase']:
                    if has_flu_in_regimen and days_since_line_start > new_chemo_agent_options['flu_dis_period']:
                        new_line_needed = True
                        regimen_status = 'New Line (Topoisomerase Addition)'
                
                # Default chemotherapy handling
                elif not is_fluoropyrimidine and has_flu_in_regimen:
                    if days_since_line_start > new_chemo_agent_options['flu_dis_period']:
                        new_line_needed = True
                        regimen_status = 'New Line (Chemo Addition to FLU)'
                    else:
                        regimen_status = 'Chemo Addition (Within Window)'
                        
            # Check for maintenance therapy transition
            if not new_line_needed and is_maintenance_therapy(current_regimen_drugs):
                regimen_status = 'Maintenance Therapy'
                
            if not regimen_status:
                regimen_status = 'Continuation'

        # Update line and regimen based on rules
        if new_line_needed:
            line_counter += 1
            current_regimen_drugs = set([drug_name])
            current_regimen = drug_name
            last_line_start_date = admin_date
            is_initial_regimen = True
            has_anti_vegf = False
            has_anti_egfr = False
        else:
            if drug_name not in current_regimen_drugs:
                current_regimen_drugs.add(drug_name)
                current_regimen = '+'.join(sorted(current_regimen_drugs))

        # Update row values
        patient_df.at[index, 'line_of_therapy'] = line_counter
        patient_df.at[index, 'regimen'] = current_regimen
        patient_df.at[index, 'line_start_date'] = last_line_start_date
        patient_df.at[index, 'line_end_date'] = admin_date
        patient_df.at[index, 'regimen_status'] = regimen_status
        patient_df.at[index, 'regimen_type'] = identify_standard_regimen(current_regimen_drugs)
        patient_df.at[index, 'maintenance_flag'] = is_maintenance_therapy(current_regimen_drugs)
        
        last_admin_date = admin_date
    
    return patient_df

def create_lot_summary(patient_df):
    """
    Create an enhanced summary of lines of therapy for a patient
    """
    summary = []
    for line_num in patient_df['line_of_therapy'].unique():
        line_data = patient_df[patient_df['line_of_therapy'] == line_num]
        
        # Get the evolution of regimens in this line
        regimen_evolution = line_data.groupby('regimen').agg({
            'administratedate': ['min', 'max'],
            'regimen_status': 'first'
        }).reset_index()
        
        summary.append({
            'patientid': line_data['patientid'].iloc[0],
            'line_of_therapy': line_num,
            'initial_regimen': line_data['regimen'].iloc[0],
            'final_regimen': line_data['regimen'].iloc[-1],
            'line_start_date': line_data['line_start_date'].iloc[0],
            'line_end_date': line_data['line_end_date'].iloc[-1],
            'duration_days': (line_data['line_end_date'].iloc[-1] - line_data['line_start_date'].iloc[0]).days,
            'num_administrations': len(line_data),
            'num_regimen_changes': len(regimen_evolution) - 1,
            'drugs_used': ', '.join(sorted(set(line_data['drugname']))),
            'regimen_evolution': regimen_evolution.to_dict('records')
        })
    
    return pd.DataFrame(summary)

def define_treatment_lines_oncology(df, gap_period_options, new_biologic_agent_options, new_chemo_agent_options, drug_interchangeability):
    """
    Main function to process all patients and create both detailed and summary outputs
    """
    # Initialize output DataFrames
    detailed_output = pd.DataFrame()
    summary_output = pd.DataFrame()
    
    # Process each patient
    for patient_id in df['patientid'].unique():
        patient_df = df[df['patientid'] == patient_id].copy()
        
        # Calculate LOT for patient
        patient_detailed = calculate_patient_lot(
            patient_df,
            gap_period_options,
            new_biologic_agent_options,
            new_chemo_agent_options,
            drug_interchangeability
        )
        
        # Create patient summary
        patient_summary = create_lot_summary(patient_detailed)
        
        # Append to output DataFrames
        detailed_output = pd.concat([detailed_output, patient_detailed])
        summary_output = pd.concat([summary_output, patient_summary])
    
    return detailed_output, summary_output