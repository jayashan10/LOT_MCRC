import pandas as pd
import numpy as np
from collections import defaultdict

def analyze_lot_patterns(detailed_df, summary_df):
    """
    Analyze Lines of Therapy patterns with focus on regimen types and treatment sequences
    """
    
    # 1. Basic Statistics
    total_patients = detailed_df.patientid.nunique()
    avg_lines = summary_df.groupby("patientid")["line_of_therapy"].max().mean()
    max_lines = summary_df.line_of_therapy.max()
    
    print("\n=== Basic Treatment Statistics ===")
    print(f"Total number of patients: {total_patients}")
    print(f"Average lines of therapy per patient: {avg_lines:.2f}")
    print(f"Maximum lines of therapy: {max_lines}")
    
    # 2. Treatment Duration Analysis by Regimen Type
    duration_stats = summary_df.groupby(["line_of_therapy", "regimen_type"])["duration_days"].agg([
        'count', 'mean', 'median', 'std'
    ]).round(1)
    print("\n=== Treatment Duration by Line and Regimen Type ===")
    print(duration_stats)
    
    # 3. Drug Category Analysis
    drug_categories = pd.crosstab(
        detailed_df.line_of_therapy,
        detailed_df.drugcategory,
        margins=True
    )
    drug_category_pct = drug_categories.div(drug_categories['All'], axis=0) * 100
    print("\n=== Drug Category Distribution by Line (%) ===")
    print(drug_category_pct.round(1))
    
    # 4. Treatment Sequence Analysis using Regimen Types
    sequences = defaultdict(int)
    for pid in summary_df.patientid.unique():
        patient_seq = summary_df[summary_df.patientid == pid].sort_values('line_of_therapy')
        seq = " -> ".join(patient_seq.regimen_type.values)
        sequences[seq] += 1
    
    print("\n=== Most Common Treatment Sequences (by Regimen Type) ===")
    for seq, count in sorted(sequences.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"{count} patients: {seq}")
    
    # 5. Line Transition Analysis using Regimen Types
    transitions = defaultdict(int)
    for pid in summary_df.patientid.unique():
        patient_lines = summary_df[summary_df.patientid == pid].sort_values('line_of_therapy')
        for i in range(len(patient_lines)-1):
            curr_regimen = patient_lines.iloc[i].regimen_type
            next_regimen = patient_lines.iloc[i+1].regimen_type
            transitions[(curr_regimen, next_regimen)] += 1
    
    print("\n=== Common Treatment Transitions ===")
    for (curr, next_), count in sorted(transitions.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"{count} patients: {curr} -> {next_}")
    
    # Add Sankey visualization
    create_sankey_visualization(summary_df)
    
    return {
        'total_patients': total_patients,
        'avg_lines': avg_lines,
        'duration_stats': duration_stats,
        'drug_categories': drug_categories,
        'sequences': sequences,
        'transitions': transitions
    }

def visualize_lot_patterns(analysis_results, output_dir='analysis/figures'):
    """
    Create visualizations for LOT patterns focusing on regimen types
    """
    import os
    import matplotlib.pyplot as plt
    import seaborn as sns
    import networkx as nx
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Treatment Duration Box Plot by Regimen Type
    plt.figure(figsize=(12, 8))
    sns.boxplot(data=summary_df, x='line_of_therapy', y='duration_days', hue='regimen_type')
    plt.title('Treatment Duration by Line of Therapy and Regimen Type')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/duration_boxplot.png')
    plt.close()
    
    # 2. Drug Category Heatmap
    plt.figure(figsize=(12, 8))
    sns.heatmap(analysis_results['drug_categories'].fillna(0), 
                annot=True, fmt='.0f', cmap='YlOrRd')
    plt.title('Drug Category Usage by Line')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/drug_category_heatmap.png')
    plt.close()
    
    # 3. Treatment Transition Network
    G = nx.DiGraph()
    for (source, target), weight in analysis_results['transitions'].items():
        if weight >= 5:  # Only show transitions with significant frequency
            G.add_edge(source, target, weight=weight)
    
    plt.figure(figsize=(15, 10))
    pos = nx.spring_layout(G, k=1, iterations=50)
    
    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_color='lightblue', 
                          node_size=[3000]*len(G.nodes))
    
    # Draw edges with varying width based on weight
    edge_weights = [G[u][v]['weight'] for u, v in G.edges()]
    nx.draw_networkx_edges(G, pos, width=[w/max(edge_weights)*3 for w in edge_weights],
                          edge_color='gray', arrows=True, arrowsize=20)
    
    # Add labels
    nx.draw_networkx_labels(G, pos, font_size=8)
    
    plt.title('Treatment Transition Network (Regimen Types)')
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/transition_network.png', bbox_inches='tight')
    plt.close()

def create_sankey_visualization(summary_df, output_dir='analysis/figures'):
    """
    Create a Sankey diagram showing treatment flows between lines of therapy
    focusing on clinically relevant regimen patterns
    """
    import plotly.graph_objects as go
    import numpy as np
    
    # Group regimens into clinically meaningful categories
    def categorize_regimen(regimen):
        if pd.isna(regimen) or regimen == 'Other':
            return 'Other'
        if 'FOLFOX' in regimen:
            return 'FOLFOX-based'
        if 'FOLFIRI' in regimen:
            return 'FOLFIRI-based'
        if 'CAPOX' in regimen:
            return 'CAPOX-based'
        if any(drug in regimen for drug in ['bevacizumab', 'aflibercept', 'ramucirumab']):
            return 'Anti-VEGF based'
        if any(drug in regimen for drug in ['cetuximab', 'panitumumab']):
            return 'Anti-EGFR based'
        if 'LONSURF' in regimen or 'Regorafenib' in regimen:
            return 'Later-line options'
        return 'Other'

    # Process data for Sankey diagram
    max_lines = min(4, summary_df.line_of_therapy.max())  # Focus on first 4 lines
    
    # Initialize nodes and links
    nodes = []
    links = {'source': [], 'target': [], 'value': []}
    
    # Create nodes for each line
    for line in range(1, max_lines + 1):
        line_data = summary_df[summary_df.line_of_therapy == line]
        regimens = line_data.regimen_type.apply(categorize_regimen).value_counts()
        
        # Add nodes for this line
        for regimen in regimens.index:
            node_name = f"L{line} {regimen}"
            nodes.append(node_name)
            
        # Create links between lines
        if line < max_lines:
            next_line = line + 1
            transitions = summary_df[
                (summary_df.line_of_therapy.isin([line, next_line])) &
                (summary_df.patientid.duplicated(keep=False))
            ].sort_values(['patientid', 'line_of_therapy'])
            
            for pid in transitions.patientid.unique():
                patient_trans = transitions[transitions.patientid == pid]
                if len(patient_trans) == 2:
                    source_reg = categorize_regimen(patient_trans.iloc[0].regimen_type)
                    target_reg = categorize_regimen(patient_trans.iloc[1].regimen_type)
                    
                    source_idx = nodes.index(f"L{line} {source_reg}")
                    target_idx = nodes.index(f"L{next_line} {target_reg}")
                    
                    links['source'].append(source_idx)
                    links['target'].append(target_idx)
                    links['value'].append(1)

    # Aggregate link values
    link_df = pd.DataFrame(links)
    link_df = link_df.groupby(['source', 'target'])['value'].sum().reset_index()

    # Create Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node = dict(
            pad = 15,
            thickness = 20,
            line = dict(color = "black", width = 0.5),
            label = nodes,
            color = "lightblue"
        ),
        link = dict(
            source = link_df.source,
            target = link_df.target,
            value = link_df.value
        )
    )])

    fig.update_layout(
        title_text="Treatment Flow Patterns Across Lines of Therapy",
        font_size=12,
        height=800
    )

    # Save the figure
    fig.write_html(f"{output_dir}/treatment_flow_sankey.html")

if __name__ == "__main__":
    # Read data
    detailed_df = pd.read_csv('output/crc_lot_detailed.csv', 
                             parse_dates=['administratedate', 'line_start_date', 'line_end_date'])
    summary_df = pd.read_csv('output/crc_lot_summary.csv', 
                            parse_dates=['line_start_date', 'line_end_date'])
    
    # Run analysis
    analysis_results = analyze_lot_patterns(detailed_df, summary_df)
    
    # Create visualizations
    visualize_lot_patterns(analysis_results)