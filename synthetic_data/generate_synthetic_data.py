import pandas as pd
import numpy as np
from datetime import timedelta, date

def generate_crc_data(num_patients=100):
    """
    Generates a synthetic dataset for mCRC patients with diverse treatment patterns.

    Args:
        num_patients (int): The number of patients to generate.

    Returns:
        pd.DataFrame: The generated DataFrame.
    """

    # --- Define Drug Lists (Consistent with config.yaml) ---
    fluoropyrimidines = ['5-fluorouracil', 'capecitabine']
    platinums = ['oxaliplatin', 'cisplatin']
    topoisomerase = ['irinotecan']
    anti_egfr = ['cetuximab', 'panitumumab']
    anti_vegf = ['bevacizumab', 'aflibercept', 'ramucirumab']
    other_targeted = ['regorafenib', 'encorafenib']
    immunotherapy = ['pembrolizumab', 'nivolumab']  # Add more if needed
    chemotherapy_other = ['leucovorin']

    all_drugs = fluoropyrimidines + platinums + topoisomerase + anti_egfr + anti_vegf + other_targeted + immunotherapy + chemotherapy_other

    # --- Define Common Regimens (for easier generation) ---
    regimens = {
        'FOLFOX': ['5-fluorouracil', 'leucovorin', 'oxaliplatin'],
        'FOLFIRI': ['5-fluorouracil', 'leucovorin', 'irinotecan'],
        'CAPOX': ['capecitabine', 'oxaliplatin'],
        'SingleAgentFLU': fluoropyrimidines,  # Can be either 5-FU or capecitabine
    }

    data = []

    for patient_id in range(1, num_patients + 1):
        current_date = date(2023, 1, 1)  # Start date for all patients
        line_start_date = current_date
        current_line = 1
        
        # --- Initial Regimen (Randomly Chosen) ---
        initial_regimen_type = np.random.choice(list(regimens.keys()))
        initial_regimen_drugs = regimens[initial_regimen_type].copy()  # Use .copy()!
        if initial_regimen_type == 'SingleAgentFLU':
             initial_regimen_drugs = [np.random.choice(initial_regimen_drugs)] #Pick only one

        # --- Maybe add a biologic/targeted agent early (with some probability) ---
        if np.random.rand() < 0.3:  # 30% chance of early biologic/targeted
            biologic_type = np.random.choice(['anti_vegf', 'anti_egfr', 'other_targeted'])
            if biologic_type == 'anti_vegf':
                initial_regimen_drugs.append(np.random.choice(anti_vegf))
            elif biologic_type == 'anti_egfr':
                initial_regimen_drugs.append(np.random.choice(anti_egfr))
            elif biologic_type == 'other_targeted':
                initial_regimen_drugs.append(np.random.choice(other_targeted))


        # --- Administer Initial Regimen (within 28-day window) ---
        for _ in range(np.random.randint(1, 4)):  # 1-3 administrations within initial window
            for drug in initial_regimen_drugs:
                category = 'chemotherapy'
                if drug in anti_egfr + anti_vegf:
                  category = 'biologics'
                if drug in other_targeted + immunotherapy:
                  category = 'targeted'
                data.append([patient_id, drug, category, current_date])
            current_date += timedelta(days=np.random.randint(5, 15))  # Vary administration intervals


        # --- Simulate Treatment Course (Multiple Lines, Various Events) ---
        num_lines = np.random.randint(1, 5)  # 1-4 lines of therapy
        for _ in range(num_lines):
            # --- Simulate a treatment duration (on current line) ---
            line_duration = np.random.randint(30, 365)  # Line duration in days
            end_date = line_start_date + timedelta(days=line_duration)

            while current_date < end_date:
                # ---  Add drugs within the line ---
                #  Pick drugs from the initial regimen (with high probability)
                #  and occasionally add or switch drugs
                current_regimen_drugs = initial_regimen_drugs.copy()

                # --- Maybe switch between interchangeable drugs ---
                if np.random.rand() < 0.2:  # 20% chance of switching
                    if any(d in current_regimen_drugs for d in fluoropyrimidines):
                        current_regimen_drugs = [d for d in current_regimen_drugs if d not in fluoropyrimidines]
                        current_regimen_drugs.append(np.random.choice(fluoropyrimidines))

                # --- Maybe add a NEW drug (with low probability) ---
                if np.random.rand() < 0.1:  # 10% chance of adding a NEW drug
                    new_drug_category = np.random.choice(['chemotherapy', 'biologics', 'targeted'])
                    if new_drug_category == 'chemotherapy':
                      new_drug_candidates = [d for d in all_drugs if d not in current_regimen_drugs and d not in immunotherapy]
                      if len(new_drug_candidates) != 0:
                        new_drug = np.random.choice(new_drug_candidates)
                        current_regimen_drugs.append(new_drug)
                    elif new_drug_category == 'biologics':
                      new_drug_candidates = [d for d in all_drugs if d not in current_regimen_drugs and (d in anti_egfr or d in anti_vegf)]
                      if len(new_drug_candidates) != 0:
                        new_drug = np.random.choice(new_drug_candidates)
                        current_regimen_drugs.append(new_drug)
                    elif new_drug_category == 'targeted':
                       new_drug_candidates = [d for d in all_drugs if d not in current_regimen_drugs and (d in other_targeted or d in immunotherapy)]
                       if len(new_drug_candidates) != 0:
                        new_drug = np.random.choice(new_drug_candidates)
                        current_regimen_drugs.append(new_drug)


                # --- Administer Current Regimen ---
                for drug in current_regimen_drugs:
                    category = 'chemotherapy'
                    if drug in anti_egfr + anti_vegf + immunotherapy:
                        category = 'biologics'
                    if drug in other_targeted:
                        category = 'targeted'
                    data.append([patient_id, drug, category, current_date])
                current_date += timedelta(days=np.random.randint(10, 28))  # Realistic intervals

            # ---  Line Change Event (Gap, New Drug, etc.) ---
            line_start_date = current_date
            # Trigger new line, after current date.

            # --- Choose a reason for line change (randomly)---
            line_change_reason = np.random.choice(['gap', 'new_chemo', 'new_biologic', 'new_targeted'])
            if line_change_reason == 'gap':
                current_date += timedelta(days=np.random.randint(181, 365))  # Long gap
            elif line_change_reason == 'new_chemo':
                # Select new chemo not in current
                available_chemo = [d for d in all_drugs if d not in current_regimen_drugs and (d in platinums or d in topoisomerase or d in fluoropyrimidines)]
                if len(available_chemo) > 0:
                  initial_regimen_drugs = [np.random.choice(available_chemo)]
                current_date += timedelta(days=np.random.randint(14, 28)) # Shorter gap
            elif line_change_reason == 'new_biologic':
                #Pick new biologic
                available_biologics = [d for d in all_drugs if d not in current_regimen_drugs and (d in anti_egfr or d in anti_vegf)]
                if len(available_biologics) > 0:
                  initial_regimen_drugs = [np.random.choice(available_biologics)]
                current_date += timedelta(days=np.random.randint(14, 28)) # Shorter gap
            elif line_change_reason == 'new_targeted':
                # Pick new targeted
                available_targeted = [d for d in all_drugs if d not in current_regimen_drugs and (d in other_targeted or d in immunotherapy)]
                if len(available_targeted) > 0:
                    initial_regimen_drugs = [np.random.choice(available_targeted)]
                current_date += timedelta(days=np.random.randint(14, 28)) # Shorter gap


    df = pd.DataFrame(data, columns=['patientid', 'drugname', 'drugcategory', 'administratedate'])
    return df.sort_values(by=['patientid', 'administratedate']).reset_index(drop=True)


if __name__ == '__main__':
    synthetic_data = generate_crc_data(num_patients=100)
    synthetic_data.to_csv('data/input_data_syn.csv', index=False)
    print("Synthetic CRC data generated and saved to data/input_data_syn.csv")

    # Example usage (optional - to check data):
    print(synthetic_data.head(20))