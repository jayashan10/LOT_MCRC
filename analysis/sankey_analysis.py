import pandas as pd
import plotly.graph_objects as go
import numpy as np

def create_sankey_diagram(summary_df, output_file='analysis/figures/treatment_sankey.html'):
    """Create an interactive Sankey diagram of treatment patterns"""
    
    # Prepare nodes and links
    nodes = set()
    links = []
    
    # Add treatment lines as nodes
    for line in range(1, summary_df.line_of_therapy.max() + 1):
        nodes.add(f"Line {line}")
    
    # Add regimens as nodes and create links
    for pid in summary_df.patientid.unique():
        patient_lines = summary_df[summary_df.patientid == pid].sort_values('line_of_therapy')
        
        for i, row in patient_lines.iterrows():
            regimen = row.initial_regimen
            line = f"Line {row.line_of_therapy}"
            nodes.add(regimen)
            links.append((line, regimen, 1))
            
            # Add transitions between lines
            if i < len(patient_lines) - 1:
                next_line = f"Line {patient_lines.iloc[i+1].line_of_therapy}"
                links.append((regimen, next_line, 1))
    
    # Convert nodes to list and create node labels
    nodes = list(nodes)
    node_indices = {node: i for i, node in enumerate(nodes)}
    
    # Aggregate link values
    link_dict = {}
    for source, target, value in links:
        key = (node_indices[source], node_indices[target])
        link_dict[key] = link_dict.get(key, 0) + value
    
    # Create Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node = dict(
            pad = 15,
            thickness = 20,
            line = dict(color = "black", width = 0.5),
            label = nodes,
            color = ["#1f77b4" if "Line" in n else "#2ca02c" for n in nodes]
        ),
        link = dict(
            source = [k[0] for k in link_dict.keys()],
            target = [k[1] for k in link_dict.keys()],
            value = list(link_dict.values()),
            color = ["rgba(169, 169, 169, 0.5)"]*len(link_dict)
        )
    )])
    
    fig.update_layout(
        title_text="Treatment Pattern Flow",
        font_size=12,
        height=600,
        width=800
    )
    
    fig.write_html(output_file)

def analyze_treatment_patterns(detailed_df, summary_df):
    """Analyze detailed treatment patterns and create visualizations"""
    
    # Create output directory
    import os
    os.makedirs('analysis/figures', exist_ok=True)
    
    # Original analysis code
    # 1. Calculate treatment durations
    duration_analysis = summary_df.groupby('line_of_therapy').agg({
        'duration_days': ['mean', 'median', 'std', 'count']
    }).round(1)
    
    # 2. Analyze regimen sequences
    sequences = summary_df.groupby('patientid').agg({
        'initial_regimen': lambda x: ' -> '.join(x),
        'line_of_therapy': 'count'
    })
    
    # 3. Analyze drug combinations
    combinations = detailed_df.groupby(['line_of_therapy', 'regimen']).size().reset_index(name='count')
    combinations = combinations.sort_values(['line_of_therapy', 'count'], ascending=[True, False])
    
    # Print results
    print("\n=== Treatment Duration Analysis ===")
    print(duration_analysis)
    
    print("\n=== Treatment Sequences ===")
    print(sequences)
    
    print("\n=== Common Drug Combinations by Line ===")
    print(combinations)
    
    # Create original Sankey diagram
    create_sankey_diagram(summary_df)
    
    # New additional visualizations
    create_alternative_visualizations(summary_df, detailed_df)

def create_alternative_visualizations(summary_df, detailed_df):
    """Create additional visualizations for treatment patterns"""
    import plotly.express as px
    import plotly.graph_objects as go
    
    # 1. Create sunburst chart of treatment patterns
    def create_sunburst():
        # Create hierarchical data structure
        sunburst_df = summary_df.copy()
        fig = px.sunburst(
            sunburst_df,
            path=['line_of_therapy', 'initial_regimen'],
            title='Treatment Patterns Hierarchy'
        )
        fig.write_html('analysis/figures/treatment_sunburst.html')
    
    # 2. Analyze and visualize common sequences
    def analyze_common_sequences():
        # Get top 10 most common treatment sequences
        sequences = summary_df.groupby('patientid').agg({
            'initial_regimen': lambda x: ' -> '.join(x)
        }).reset_index()
        
        sequence_counts = sequences['initial_regimen'].value_counts().head(10)
        
        fig = go.Figure(data=[
            go.Bar(x=sequence_counts.values,
                  y=sequence_counts.index,
                  orientation='h')
        ])
        
        fig.update_layout(
            title='Top 10 Most Common Treatment Sequences',
            xaxis_title='Number of Patients',
            yaxis_title='Treatment Sequence',
            height=800,
            width=1000
        )
        
        fig.write_html('analysis/figures/common_sequences.html')
    
    # 3. Create treatment duration boxplot
    def create_duration_boxplot():
        fig = px.box(
            summary_df,
            x='line_of_therapy',
            y='duration_days',
            color='initial_regimen',
            title='Treatment Duration by Line and Regimen'
        )
        
        fig.update_layout(
            height=600,
            width=1000,
            showlegend=True
        )
        
        fig.write_html('analysis/figures/duration_boxplot.html')
    
    # Generate all new visualizations
    try:
        create_sunburst()
        analyze_common_sequences()
        create_duration_boxplot()
        print("\nAdditional visualizations created successfully in 'analysis/figures/' directory")
    except Exception as e:
        print(f"\nError creating additional visualizations: {str(e)}")

if __name__ == "__main__":
    # Read data
    detailed_df = pd.read_csv('output/crc_lot_detailed.csv', parse_dates=['administratedate', 'line_start_date', 'line_end_date'])
    summary_df = pd.read_csv('output/crc_lot_summary.csv', parse_dates=['line_start_date', 'line_end_date'])
    
    # Run analysis
    analyze_treatment_patterns(detailed_df, summary_df) 