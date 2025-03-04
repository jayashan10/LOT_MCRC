import pandas as pd
from timeline_viewer import TimelineViewer
import argparse

def load_processed_data():
    """Load the already processed detailed LOT data"""
    try:
        detailed_df = pd.read_csv('output/crc_lot_detailed.csv', parse_dates=['administratedate'])
        detailed_df['patientid'] = detailed_df['patientid'].astype(int)
        return detailed_df
    except FileNotFoundError:
        print("Error: Detailed data file not found. Please run LOT analysis first.")
        return None

def load_summary_data():
    """Load the already processed summary LOT data"""
    try:
        summary_df = pd.read_csv('output/crc_lot_summary.csv', parse_dates=['line_start_date', 'line_end_date'])
        summary_df['patientid'] = summary_df['patientid'].astype(int)
        return summary_df
    except FileNotFoundError:
        print("Warning: Summary data file not found. Continuing without summary details.")
        return None

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='View timeline for a specific patient')
    parser.add_argument('patient_id', type=int, help='Patient ID (integer) to view timeline for')
    args = parser.parse_args()

    # Load the processed detailed and summary data
    detailed_df = load_processed_data()
    if detailed_df is None:
        return
    summary_df = load_summary_data()

    if args.patient_id not in detailed_df['patientid'].values:
        print(f"Error: Patient {args.patient_id} not found in the detailed data")
        return

    # Initialize timeline viewer with both detailed and summary outputs
    viewer = TimelineViewer(detailed_df, summary_df)
    timeline_file = viewer.view_patient_timeline(args.patient_id)
    
    if timeline_file:
        print(f"\nTimeline generated successfully!")
        print(f"Open this file in your web browser: {timeline_file}")

if __name__ == "__main__":
    main()