import pandas as pd

def calculate_patient_lot(patient_df, gap_period_options, new_biologic_agent_options, new_chemo_agent_options, drug_interchangeability):
    """
    Calculate lines of therapy for a single patient incorporating both 28-day window
    and CRC-specific rules with enhanced drug handling.
    """
    # Initialize patient's first treatment
    line_counter = 1
    current_regimen_drugs = set()
    last_admin_date = None
    last_line_start_date = None
    current_regimen = None
    in_initial_window = True  # Track if we're in 28-day window
    current_window_end = None
    
    # --- TRACK UNIQUE BIOLOGIC/TARGETED DRUGS ---
    biologic_targeted_drugs = set()

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
    patient_df['regimen_type'] = ''  # For standard regimen types
    patient_df['maintenance_flag'] = False
    patient_df['days_from_first_line'] = 0
    patient_df['days_from_prev_treatment'] = 0
    patient_df['in_initial_window'] = False  # New column to track 28-day window
    
    # Process all administrations
    for idx, row in patient_df.iterrows():
        current_date = row['administratedate']
        
        # If this is the first administration or start of a new line
        if last_line_start_date is None or (last_line_start_date == current_date and idx > 0):
            last_line_start_date = current_date
            current_window_end = current_date + pd.Timedelta(days=28)
            in_initial_window = True
            if idx == 0:  # First administration for patient
                current_regimen_drugs = {row['drugname']}
            
        # Calculate days from line start and previous treatment
        days_since_line_start = (current_date - last_line_start_date).days
        days_since_last_admin = (current_date - last_admin_date).days if last_admin_date else 0
        
        # Update initial window status
        in_initial_window = current_date <= current_window_end
        patient_df.loc[idx, 'in_initial_window'] = in_initial_window
        
        # Process administration
        if idx == 0:  # First administration
            patient_df.loc[idx, 'line_of_therapy'] = line_counter
            patient_df.loc[idx, 'regimen_status'] = 'Initial Regimen'
        else:
            new_line_needed, regimen_status = process_subsequent_administrations(
                row, current_regimen_drugs, last_admin_date, last_line_start_date,
                biologic_targeted_drugs, drug_interchangeability,
                new_biologic_agent_options, new_chemo_agent_options,
                gap_period_options, in_initial_window
            )
            
            if new_line_needed:
                line_counter += 1
                current_regimen_drugs = {row['drugname']}
                last_line_start_date = current_date
                current_window_end = current_date + pd.Timedelta(days=28)
                in_initial_window = True
                patient_df.loc[idx, 'in_initial_window'] = True
                patient_df.loc[idx, 'days_from_first_line'] = 0
            else:
                current_regimen_drugs.add(row['drugname'])
                patient_df.loc[idx, 'days_from_first_line'] = days_since_line_start
            
            patient_df.loc[idx, 'line_of_therapy'] = line_counter
            patient_df.loc[idx, 'regimen_status'] = regimen_status
        
        # Update common fields
        current_regimen = '+'.join(sorted(current_regimen_drugs))
        current_regimen_type = identify_standard_regimen(current_regimen_drugs)
        
        patient_df.loc[idx, 'regimen'] = current_regimen
        patient_df.loc[idx, 'line_start_date'] = last_line_start_date
        patient_df.loc[idx, 'line_end_date'] = current_date
        patient_df.loc[idx, 'regimen_type'] = current_regimen_type if current_regimen_type else 'Other'
        patient_df.loc[idx, 'maintenance_flag'] = is_maintenance_therapy(current_regimen_drugs, drug_interchangeability)
        patient_df.loc[idx, 'days_from_prev_treatment'] = days_since_last_admin
        
        # Track biologic/targeted drugs
        if row['drugcategory'] in ('biologics', 'targeted'):
            biologic_targeted_drugs.add(row['drugname'])
        
        last_admin_date = current_date
    
    return patient_df

def process_subsequent_administrations(row, current_regimen_drugs, last_admin_date, last_line_start_date, 
                                    biologic_targeted_drugs, drug_interchangeability, 
                                    new_biologic_agent_options, new_chemo_agent_options,
                                    gap_period_options, in_initial_window):
    """
    Process each administration after the initial period to determine if a new line should be started
    """
    drug_name = row['drugname']
    admin_date = row['administratedate']
    drug_category = row['drugcategory']
    
    days_since_line_start = (admin_date - last_line_start_date).days
    days_since_last_admin = (admin_date - last_admin_date).days
    
    new_line_needed = False
    regimen_status = ''
    
    # 1. Treatment Gap Rule
    if days_since_last_admin > gap_period_options['gap_treatment_restart']:
        new_line_needed = True
        regimen_status = 'New Line (Gap)'
    
    elif drug_name in current_regimen_drugs:
        regimen_status = 'Continuation'
    
    # 2. Biologic Rules
    elif drug_category in ('biologics', 'targeted'):
        if drug_name not in biologic_targeted_drugs:
            biologic_targeted_drugs.add(drug_name)
            
            if len(biologic_targeted_drugs) >= 2:
                new_line_needed = True
                regimen_status = 'New Line (Second Biologic/Targeted Agent Added)'
            else:
                if drug_name in drug_interchangeability['CRC']['anti_vegf']:
                    if days_since_line_start > new_biologic_agent_options['after_initial_period']:
                        new_line_needed = True
                        regimen_status = 'New Line (Anti-VEGF Addition)'
                    else:
                        regimen_status = 'Anti-VEGF Addition (Within Window)'
                
                elif drug_name in drug_interchangeability['CRC']['anti_egfr']:
                    if days_since_line_start > new_biologic_agent_options['bio_dis1_period']:
                        new_line_needed = True
                        regimen_status = 'New Line (EGFR Addition/Switch)'
                    else:
                        regimen_status = 'EGFR Addition (Within Window)'
                
                elif drug_name in drug_interchangeability['CRC']['other_targeted']:
                    if days_since_line_start > new_biologic_agent_options['bio_dis1_period']:
                        new_line_needed = True
                        regimen_status = 'New Line (Other Targeted Addition)'
                    else:
                        regimen_status = 'Other Targeted Addition (Within Window)'
    
    # 3. New Chemotherapy Agent Rules
    elif drug_category == 'chemotherapy':
        if drug_name not in current_regimen_drugs:
            # During initial window, allow combinations
            if in_initial_window:
                regimen_status = 'New Chemo Addition (Initial Window)'
            # After initial window, check single regimen rule
            elif not can_add_new_chemotherapy(current_regimen_drugs, drug_name, drug_interchangeability):
                new_line_needed = True
                regimen_status = 'New Line (Invalid Chemo Addition)'
            elif days_since_line_start > new_chemo_agent_options['flu_dis_period']:
                new_line_needed = True
                regimen_status = 'New Line (New Chemo Addition)'
            else:
                regimen_status = 'New Chemo Addition (Within Window)'
    
    return new_line_needed, regimen_status

def is_single_fluoropyrimidine_regimen(drugs, drug_interchangeability):
    """
    Check if the current regimen is a single fluoropyrimidine agent regimen.
    
    Args:
        drugs (set): Set of current drugs in the regimen
        drug_interchangeability (dict): Drug interchangeability rules
        
    Returns:
        bool: True if regimen contains only fluoropyrimidine(s), False otherwise
    """
    flu_agents = set(drug_interchangeability['CRC']['fluoropyrimidines'])
    chemo_drugs = set()
    
    # Get all chemotherapy drugs
    for category in drug_interchangeability['CRC']['chemotherapy'].values():
        chemo_drugs.update(category)
    
    # Check if all drugs are either fluoropyrimidines or supportive care (like leucovorin)
    non_supportive_drugs = {drug for drug in drugs if drug != 'leucovorin'}
    return all(drug in flu_agents for drug in non_supportive_drugs)

def can_add_new_chemotherapy(current_drugs, new_drug, drug_interchangeability):
    """
    Determine if a new chemotherapy agent can be added based on clinical rules.
    
    Args:
        current_drugs (set): Current drugs in the regimen
        new_drug (str): New drug being considered for addition
        drug_interchangeability (dict): Drug interchangeability rules
        
    Returns:
        bool: True if new chemotherapy can be added, False otherwise
    """
    # If current regimen is not a single fluoropyrimidine, don't allow new chemo
    if not is_single_fluoropyrimidine_regimen(current_drugs, drug_interchangeability):
        return False
        
    # Check if new drug is a chemotherapy agent
    chemo_drugs = set()
    for category in drug_interchangeability['CRC']['chemotherapy'].values():
        chemo_drugs.update(category)
    
    if new_drug not in chemo_drugs:
        return True  # Not a chemo drug, so no restriction
        
    # Allow addition if it forms a standard regimen
    potential_regimen = current_drugs | {new_drug}
    for regimen_drugs in drug_interchangeability['CRC']['standard_regimens'].values():
        if set(regimen_drugs) == potential_regimen:
            return True
            
    return False

def identify_standard_regimen(drugs):
    """
    Helper function to identify standard regimens in colorectal cancer treatment
    
    Standard regimens identified:
    - FOLFOX: 5-FU/LV (Fluorouracil/Leucovorin) + Oxaliplatin
        - mFOLFOX6: Modified FOLFOX6 regimen
        - FOLFOX4: Standard FOLFOX4 regimen
    - FOLFIRI: 5-FU/LV + Irinotecan
    - FOLFOXIRI/FOLFIRINOX: 5-FU/LV + Oxaliplatin + Irinotecan
    - Capecitabine-based:
        - CAPOX/XELOX (Capecitabine + Oxaliplatin)
        - CAPIRI/XELIRI (Capecitabine + Irinotecan)
    - Fluoropyrimidine monotherapy:
        - 5-FU/LV (Fluorouracil + Leucovorin)
        - Capecitabine alone
    - Later-line options:
        - LONSURF (Trifluridine/Tipiracil)
        - Regorafenib
    - Targeted therapy combinations:
        - Anti-VEGF: bevacizumab, aflibercept, ramucirumab
        - Anti-EGFR: cetuximab, panitumumab
        
    Args:
        drugs (set): Set of drug names in the current regimen
            
    Returns:
        str: Identified standard regimen name or None if no standard regimen matches
    """
    drug_set = set(map(str.lower, drugs))  # Convert to lowercase for case-insensitive matching
        
    # Define standard regimen components
    fluoropyrimidines = {
        'fluorouracil', '5-fluorouracil', '5-fu', 'fu', 
        'capecitabine', 'xeloda'
    }
    leucovorin = {'leucovorin', 'folinic acid', 'lv', 'calcium folinate'}
    lonsurf_components = {'trifluridine', 'tipiracil'}
        
    # Define targeted therapy groups
    anti_vegf = {'bevacizumab', 'aflibercept', 'ramucirumab'}
    anti_egfr = {'cetuximab', 'panitumumab'}
    other_targeted = {'regorafenib'}
        
    # Check for base components
    has_fluoropyrimidine = any(drug in drug_set for drug in fluoropyrimidines)
    has_leucovorin = any(drug in drug_set for drug in leucovorin)
    has_oxaliplatin = 'oxaliplatin' in drug_set
    has_irinotecan = 'irinotecan' in drug_set
    has_lonsurf = all(drug in drug_set for drug in lonsurf_components)
        
    # Check for targeted therapies
    has_anti_vegf = any(drug in drug_set for drug in anti_vegf)
    has_anti_egfr = any(drug in drug_set for drug in anti_egfr)
    has_regorafenib = 'regorafenib' in drug_set
        
    # Helper function to check for 5-FU variations
    def has_5fu():
        return any(drug in drug_set for drug in {'fluorouracil', '5-fluorouracil', '5-fu', 'fu'})
        
    # Initialize base_regimen
    base_regimen = None
        
    # First check for LONSURF as it's a specific combination
    if has_lonsurf:
        base_regimen = 'LONSURF'
    # Then check other base regimens
    elif has_fluoropyrimidine:
        if has_oxaliplatin and has_irinotecan and has_leucovorin:
            base_regimen = 'FOLFOXIRI'  # also known as FOLFIRINOX
        elif has_oxaliplatin and has_leucovorin:
            if has_5fu():
                base_regimen = 'FOLFOX'
        elif has_irinotecan and has_leucovorin:
            if has_5fu():
                base_regimen = 'FOLFIRI'
        elif 'capecitabine' in drug_set or 'xeloda' in drug_set:
            if has_oxaliplatin:
                base_regimen = 'CAPOX'  # also known as XELOX
            elif has_irinotecan:
                base_regimen = 'CAPIRI'  # also known as XELIRI
            else:
                base_regimen = 'Capecitabine'
        elif has_leucovorin:
            base_regimen = '5-FU/LV'
        else:
            base_regimen = '5-FU'
    elif has_regorafenib:
        base_regimen = 'Regorafenib'
        
    # Add targeted therapy to regimen name
    targeted_components = []
    if has_anti_vegf:
        anti_vegf_drugs = [drug for drug in anti_vegf if drug in drug_set]
        targeted_components.extend(anti_vegf_drugs)
    if has_anti_egfr:
        anti_egfr_drugs = [drug for drug in anti_egfr if drug in drug_set]
        targeted_components.extend(anti_egfr_drugs)
        
    # Format final regimen name
    if base_regimen:
        if targeted_components:
            return f"{base_regimen} + {' + '.join(targeted_components)}"
        return base_regimen
        
    # Handle single agent targeted therapies
    if len(drug_set) == 1:
        drug = drug_set.pop()
        if drug in anti_vegf or drug in anti_egfr:
            return drug.capitalize()
        
    # If multiple targeted agents without chemotherapy backbone
    if targeted_components:
        return ' + '.join(drug.capitalize() for drug in targeted_components)
        
    # If no standard regimen is identified
    return None
    
def is_maintenance_therapy(drugs, drug_interchangeability):
    """
    Helper function to identify maintenance therapy
    
    Args:
        drugs: Set of drugs to check
        drug_interchangeability: Rules for drug interchangeability
    
    Returns:
        bool: True if the drug combination is a maintenance therapy
    """
    drug_set = set(drugs)
    for maintenance in drug_interchangeability['CRC']['sequence_rules']['maintenance_options']:
        maint_drugs = set(maintenance.split('+'))
        if maint_drugs.issubset(drug_set):
            return True
    return False

def create_lot_summary(patient_df):
    """
    Create an enhanced summary of lines of therapy for a patient
    
    Args:
        patient_df (pd.DataFrame): Patient's treatment data with line assignments
        
    Returns:
        pd.DataFrame: Summary of each line of therapy
    """
    summary_data = []
    
    for line_num in sorted(patient_df['line_of_therapy'].unique()):
        if line_num == 0:  # Skip unassigned treatments
            continue
            
        line_data = patient_df[patient_df['line_of_therapy'] == line_num]
        
        # Get unique drugs in the line
        drugs_in_line = sorted(set(line_data['drugname']))
        regimen_str = '+'.join(drugs_in_line)
        
        # Get the standard regimen name if available
        standard_regimen = identify_standard_regimen(set(drugs_in_line))
        
        summary_data.append({
            'patientid': line_data['patientid'].iloc[0],
            'line_of_therapy': line_num,
            'line_start_date': line_data['line_start_date'].iloc[0],
            'line_end_date': line_data['line_end_date'].iloc[-1],
            'duration_days': (line_data['line_end_date'].iloc[-1] - line_data['line_start_date'].iloc[0]).days,
            'num_administrations': len(line_data),
            'drugs': regimen_str,
            'regimen_type': standard_regimen if standard_regimen else 'Other',
            'maintenance_flag': any(line_data['maintenance_flag'])
        })
    
    return pd.DataFrame(summary_data)

def define_treatment_lines_oncology(df, gap_period_options, new_biologic_agent_options, new_chemo_agent_options, drug_interchangeability):
    """
    Main function to process all patients and create both detailed and summary outputs
    """
    # Initialize output dataframes
    detailed_output = pd.DataFrame()
    summary_output = pd.DataFrame()
    
    # Process each patient
    for patient_id in df['patientid'].unique():
        patient_df = df[df['patientid'] == patient_id].sort_values('administratedate').reset_index(drop=True)
        
        # Calculate lines of therapy
        patient_detailed = calculate_patient_lot(
            patient_df,
            gap_period_options,
            new_biologic_agent_options,
            new_chemo_agent_options,
            drug_interchangeability
        )
        
        # Create summary
        patient_summary = create_lot_summary(patient_detailed)
        
        # Append to output
        detailed_output = pd.concat([detailed_output, patient_detailed], ignore_index=True)
        summary_output = pd.concat([summary_output, patient_summary], ignore_index=True)
    
    return detailed_output, summary_output