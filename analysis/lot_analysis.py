import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict

def analyze_lot_patterns(detailed_df, summary_df):
    """Analyze Lines of Therapy patterns"""
    
    # 1. Basic Statistics
    total_patients = detailed_df.patientid.nunique()
    avg_lines = summary_df.groupby("patientid")["line_of_therapy"].max().mean()
    max_lines = summary_df.line_of_therapy.max()
    
    print("\n=== Basic Treatment Statistics ===")
    print(f"Total number of patients: {total_patients}")
    print(f"Average lines of therapy per patient: {avg_lines:.2f}")
    print(f"Maximum lines of therapy: {max_lines}")
    
    # 2. Treatment Duration Analysis
    duration_stats = summary_df.groupby("line_of_therapy")["duration_days"].agg(['mean', 'median', 'std']).round(1)
    print("\n=== Treatment Duration by Line ===")
    print(duration_stats)
    
    # 3. Drug Category Analysis
    drug_categories = detailed_df.groupby(["line_of_therapy", "drugcategory"]).size().unstack(fill_value=0)
    drug_category_pct = drug_categories.div(drug_categories.sum(axis=1), axis=0) * 100
    print("\n=== Drug Category Distribution by Line (%) ===")
    print(drug_category_pct.round(1))
    
    # 4. Treatment Sequence Analysis
    sequences = defaultdict(int)
    for pid in summary_df.patientid.unique():
        patient_seq = summary_df[summary_df.patientid == pid].sort_values('line_of_therapy')
        seq = " -> ".join(patient_seq.initial_regimen.values)
        sequences[seq] += 1
    
    print("\n=== Most Common Treatment Sequences ===")
    for seq, count in sorted(sequences.items(), key=lambda x: x[1], reverse=True):
        print(f"{count} patients: {seq}")
    
    # 5. Line Transition Analysis
    transitions = defaultdict(int)
    for pid in summary_df.patientid.unique():
        patient_lines = summary_df[summary_df.patientid == pid].sort_values('line_of_therapy')
        for i in range(len(patient_lines)-1):
            curr_regimen = patient_lines.iloc[i].final_regimen
            next_regimen = patient_lines.iloc[i+1].initial_regimen
            transitions[(curr_regimen, next_regimen)] += 1
    
    print("\n=== Common Treatment Transitions ===")
    for (curr, next_), count in sorted(transitions.items(), key=lambda x: x[1], reverse=True):
        print(f"{count} patients: {curr} -> {next_}")
    
    # 6. Regimen Type Analysis
    regimen_types = detailed_df.groupby(["line_of_therapy", "regimen_type"]).size().unstack(fill_value=0)
    regimen_type_pct = regimen_types.div(regimen_types.sum(axis=1), axis=0) * 100
    print("\n=== Regimen Type Distribution by Line (%) ===")
    print(regimen_type_pct.round(1))
    
    return {
        'total_patients': total_patients,
        'avg_lines': avg_lines,
        'duration_stats': duration_stats,
        'drug_categories': drug_categories,
        'sequences': sequences,
        'transitions': transitions,
        'regimen_types': regimen_types
    }

def visualize_lot_patterns(analysis_results, output_dir='analysis/figures'):
    """Create visualizations for LOT patterns"""
    
    # Create output directory if it doesn't exist
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Treatment Duration Box Plot
    plt.figure(figsize=(10, 6))
    sns.boxplot(data=summary_df, x='line_of_therapy', y='duration_days')
    plt.title('Treatment Duration by Line of Therapy')
    plt.savefig(f'{output_dir}/duration_boxplot.png')
    plt.close()
    
    # 2. Drug Category Heatmap
    plt.figure(figsize=(12, 8))
    sns.heatmap(analysis_results['drug_categories'], annot=True, fmt='d', cmap='YlOrRd')
    plt.title('Drug Category Usage by Line of Therapy')
    plt.savefig(f'{output_dir}/drug_category_heatmap.png')
    plt.close()
    
    # 3. Treatment Sequence Network (simplified version)
    transitions = analysis_results['transitions']
    plt.figure(figsize=(15, 10))
    
    # Create network layout (simplified)
    from networkx import DiGraph, spring_layout
    import networkx as nx
    
    G = DiGraph()
    for (source, target), weight in transitions.items():
        G.add_edge(source, target, weight=weight)
    
    pos = spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_color='lightblue', 
            node_size=2000, font_size=8, font_weight='bold',
            arrows=True, edge_color='gray')
    
    plt.title('Treatment Transition Network')
    plt.savefig(f'{output_dir}/transition_network.png')
    plt.close()

if __name__ == "__main__":
    # Read data
    detailed_df = pd.read_csv('output/crc_lot_detailed.csv', parse_dates=['administratedate', 'line_start_date', 'line_end_date'])
    summary_df = pd.read_csv('output/crc_lot_summary.csv', parse_dates=['line_start_date', 'line_end_date'])
    
    # Run analysis
    analysis_results = analyze_lot_patterns(detailed_df, summary_df)
    
    # Create visualizations
    visualize_lot_patterns(analysis_results) 