import pandas as pd
import plotly.graph_objects as go
import numpy as np

def create_sankey_diagram(summary_df, output_file='analysis/figures/treatment_sankey.html', threshold_pct=2):
    """
    Create a sequential Sankey diagram showing treatment flows between lines of therapy
    
    Args:
        summary_df: DataFrame with treatment summary data
        output_file: Path to save the HTML output
        threshold_pct: Minimum percentage of patients for a regimen to be shown separately (default 5%)
    """
    import plotly.graph_objects as go
    
    # Process data
    max_lines = min(4, summary_df.line_of_therapy.max())
    nodes = []
    links = {'source': [], 'target': [], 'value': [], 'customdata': []}
    node_indices = {}
    
    # Create a copy of summary_df to modify regimen_type
    plot_df = summary_df.copy()
    
    # Group small regimens into "Others" for each line
    for line in range(1, max_lines + 1):
        line_data = plot_df[plot_df.line_of_therapy == line]
        
        # Calculate total patients in this line
        line_total_patients = len(line_data.patientid.unique())
        threshold_count = line_total_patients * threshold_pct / 100
        
        regimen_counts = line_data.regimen_type.value_counts()
        
        # Identify regimens below threshold
        small_regimens = regimen_counts[regimen_counts < threshold_count].index
        
        # Replace small regimens with "Others"
        if not small_regimens.empty:
            plot_df.loc[(plot_df.line_of_therapy == line) & 
                       (plot_df.regimen_type.isin(small_regimens)), 
                       'regimen_type'] = 'Others'
    
    # Create nodes for each line of therapy
    for line in range(1, max_lines + 1):
        line_data = plot_df[plot_df.line_of_therapy == line]
        line_total = len(line_data.patientid.unique())  # Get total patients for this line
        
        # Get regimen counts
        regimen_counts = line_data.regimen_type.value_counts()
        
        # Separate 'Others' from other regimens
        others_count = regimen_counts.get('Others', 0)
        regular_regimens = regimen_counts[regimen_counts.index != 'Others'].sort_values(ascending=False)
        
        # Add regular regimens first, in descending order
        for regimen, count in regular_regimens.items():
            node_name = f"L{line} {regimen}"
            node_indices[node_name] = len(nodes)
            nodes.append({
                'name': node_name,
                'count': count,
                'percent': f"{(count/line_total)*100:.1f}%"  # Calculate percentage based on line total
            })
        
        # Add 'Others' at the end, if it exists
        if others_count > 0:
            node_name = f"L{line} Others"
            node_indices[node_name] = len(nodes)
            nodes.append({
                'name': node_name,
                'count': others_count,
                'percent': f"{(others_count/line_total)*100:.1f}%"
            })
    
    # Create links between lines using modified DataFrame
    for line in range(1, max_lines):
        transitions = plot_df[
            (plot_df.line_of_therapy.isin([line, line+1])) &
            (plot_df.patientid.duplicated(keep=False))
        ].sort_values(['patientid', 'line_of_therapy'])
        
        # Calculate total patients in this line for percentage
        line_total = len(plot_df[plot_df.line_of_therapy == line].patientid.unique())
        
        # Group transitions
        transition_counts = transitions.groupby('patientid').agg({
            'regimen_type': lambda x: tuple(x)
        }).reset_index()
        
        # Count each transition pattern
        pattern_counts = transition_counts.groupby('regimen_type').size()
        
        for trans_pattern, count in pattern_counts.items():
            if len(trans_pattern) == 2:
                source = f"L{line} {trans_pattern[0]}"
                target = f"L{line+1} {trans_pattern[1]}"
                
                if source in node_indices and target in node_indices:
                    links['source'].append(node_indices[source])
                    links['target'].append(node_indices[target])
                    links['value'].append(count)
                    links['customdata'].append(f"{count} patients ({(count/line_total)*100:.1f}%)")
    
    # Create color scheme with additional color for "Others"
    node_colors = []
    for node in nodes:
        name = node['name']
        if 'Others' in name:
            color = '#7f7f7f'  # gray for Others
        elif 'FOLFOX' in name:
            color = '#1f77b4'  # blue
        elif 'FOLFIRI' in name:
            color = '#2ca02c'  # green
        elif 'CAPOX' in name:
            color = '#ff7f0e'  # orange
        elif any(x in name for x in ['LONSURF', 'Regorafenib', 'Fruquintinib']):
            color = '#d62728'  # red
        elif 'Fluoropyrimidine' in name:
            color = '#9467bd'  # purple
        elif any(x in name for x in ['Bevacizumab', 'Cetuximab', 'Panitumumab']):
            color = '#8c564b'  # brown
        else:
            color = '#7f7f7f'  # gray
        node_colors.append(color)
    
    # Create Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node = dict(
            pad = 15,
            thickness = 20,
            line = dict(color = "black", width = 0.5),
            label = [f"{n['name']}<br>{n['count']} ({n['percent']})" for n in nodes],
            color = node_colors,
            hovertemplate = "%{label}<extra></extra>"
        ),
        link = dict(
            source = links['source'],
            target = links['target'],
            value = links['value'],
            customdata = links['customdata'],
            hovertemplate = 'From %{source.label}<br>To %{target.label}<br>%{customdata}<extra></extra>',
            color = ['rgba(169,169,169,0.3)'] * len(links['source'])
        )
    )])
    
    fig.update_layout(
        title_text="Sequential Treatment Patterns in mCRC",
        font_size=12,
        height=800,
        width=1200
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
        'regimen_type': lambda x: ' -> '.join(x),
        'line_of_therapy': 'count'
    })
    
    # 3. Analyze drug combinations
    combinations = detailed_df.groupby(['line_of_therapy', 'regimen_type']).size().reset_index(name='count')
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
        fig = px.sunburst(
            summary_df,
            path=['line_of_therapy', 'regimen_type'],
            title='Treatment Patterns Hierarchy'
        )
        fig.write_html('analysis/figures/treatment_sunburst.html')
    
    # 2. Analyze and visualize common sequences
    def analyze_common_sequences():
        sequences = summary_df.groupby('patientid').agg({
            'regimen_type': lambda x: ' -> '.join(x)
        }).reset_index()
        
        sequence_counts = sequences['regimen_type'].value_counts().head(10)
        
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
            color='regimen_type',
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