import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from collections import defaultdict
import networkx as nx
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def preprocess_data(detailed_df, summary_df, min_patient_threshold=0.01):
    """
    Preprocess data for visualization with smart filtering and grouping
    
    Parameters:
    -----------
    detailed_df : pd.DataFrame
        Detailed treatment data
    summary_df : pd.DataFrame
        Summary treatment data
    min_patient_threshold : float
        Minimum percentage of patients for including a treatment pattern
    """
    # Calculate total patients
    total_patients = detailed_df.patientid.nunique()
    min_patients = max(int(total_patients * min_patient_threshold), 1)
    
    # Group similar treatments based on clinical knowledge
    def standardize_regimen(regimen):
        if pd.isna(regimen):
            return "Unknown"
        parts = sorted(regimen.split('+'))
        # Group common combination therapies
        if 'fluorouracil' in regimen.lower() and 'leucovorin' in regimen.lower():
            if 'oxaliplatin' in regimen.lower():
                return 'FOLFOX'
            elif 'irinotecan' in regimen.lower():
                return 'FOLFIRI'
        elif 'capecitabine' in regimen.lower() and 'oxaliplatin' in regimen.lower():
            return 'CAPOX'
        elif 'bevacizumab' in regimen.lower():
            base = regimen.lower().replace('bevacizumab', '').replace('+', '').strip()
            if 'folfox' in base:
                return 'FOLFOX-Bev'
            elif 'folfiri' in base:
                return 'FOLFIRI-Bev'
        # Group by drug class if too specific
        if len(parts) > 2:
            drug_classes = detailed_df[detailed_df['regimen'] == regimen]['drugcategory'].unique()
            return '+'.join(sorted(set(drug_classes)))
        return regimen
    
    # Create hierarchical drug classifications
    detailed_df['drug_class'] = detailed_df['drugcategory'].fillna('Unknown')
    detailed_df['standardized_regimen'] = detailed_df['regimen'].apply(standardize_regimen)
    
    # Filter rare combinations (less than min_patient_threshold% of patients)
    regimen_counts = summary_df.groupby('initial_regimen').size()
    common_regimens = regimen_counts[regimen_counts >= min_patients].index
    
    # Add time-based features - convert to string format for JSON serialization
    summary_df['year_quarter'] = pd.to_datetime(summary_df['line_start_date']).dt.strftime('%Y-Q%q')
    detailed_df['year_quarter'] = pd.to_datetime(detailed_df['administratedate']).dt.strftime('%Y-Q%q')
    
    # Pre-calculate some common aggregations for better performance
    summary_stats = {
        'total_patients': total_patients,
        'common_regimens': common_regimens,
        'time_periods': sorted(summary_df['year_quarter'].unique()),
        'regimen_counts': regimen_counts
    }
    
    return detailed_df, summary_df, summary_stats

def create_dashboard(detailed_df, summary_df):
    """Create the interactive dashboard"""
    app = dash.Dash(__name__)
    
    # Preprocess data
    preprocessed_detailed, preprocessed_summary, summary_stats = preprocess_data(detailed_df, summary_df)
    
    app.layout = html.Div([
        html.H1("Metastatic Colorectal Cancer Treatment Patterns"),
        
        html.Div([
            html.Div([
                html.Label('Lines of Therapy:'),
                dcc.Dropdown(
                    id='line-filter',
                    options=[{'label': f'Line {i}', 'value': i} 
                            for i in sorted(preprocessed_summary.line_of_therapy.unique())],
                    value=list(preprocessed_summary.line_of_therapy.unique()),
                    multi=True
                ),
            ], style={'width': '48%', 'display': 'inline-block'}),
            
            html.Div([
                html.Label('Drug Classes:'),
                dcc.Dropdown(
                    id='drug-class-filter',
                    options=[{'label': cat, 'value': cat} 
                            for cat in sorted(preprocessed_detailed.drugcategory.unique())],
                    value=list(preprocessed_detailed.drugcategory.unique()),
                    multi=True
                ),
            ], style={'width': '48%', 'display': 'inline-block', 'float': 'right'})
        ]),
        
        html.Div([
            html.Div([
                html.H3("Treatment Flow Patterns"),
                dcc.Graph(id='sankey-overview')
            ], className='six columns'),
            
            html.Div([
                html.H3("Treatment Statistics"),
                html.Div(id='stats-table')
            ], className='six columns'),
        ], className='row'),
        
        html.Div([
            html.Div([
                html.H3("Duration Analysis by Line of Therapy"),
                dcc.Graph(id='duration-analysis')
            ], className='six columns'),
            
            html.Div([
                html.H3("Drug Category Distribution"),
                dcc.Graph(id='category-distribution')
            ], className='six columns'),
        ], className='row'),
        
        html.Div([
            html.Div([
                html.H3("Treatment Sequence Analysis"),
                dcc.Graph(id='sequence-analysis')
            ], className='six columns'),
            
            html.Div([
                html.H3("Temporal Treatment Patterns"),
                dcc.Graph(id='temporal-patterns')
            ], className='six columns'),
        ], className='row'),
    ])
    
    @app.callback(
        [Output('sankey-overview', 'figure'),
         Output('stats-table', 'children'),
         Output('duration-analysis', 'figure'),
         Output('category-distribution', 'figure'),
         Output('sequence-analysis', 'figure'),
         Output('temporal-patterns', 'figure')],
        [Input('line-filter', 'value'),
         Input('drug-class-filter', 'value')]
    )
    def update_graphs(selected_lines, selected_drug_classes):
        """Update all graphs based on selected filters"""
        try:
            # Filter data based on selections and use summary_stats for smart filtering
            filtered_summary = preprocessed_summary[
                (preprocessed_summary.line_of_therapy.isin(selected_lines)) &
                (preprocessed_summary.initial_regimen.isin(summary_stats['common_regimens']))
            ].copy()
            
            filtered_detailed = preprocessed_detailed[
                (preprocessed_detailed.line_of_therapy.isin(selected_lines)) &
                (preprocessed_detailed.drugcategory.isin(selected_drug_classes))
            ].copy()
            
            # Create visualizations with enhanced context from summary_stats
            sankey_fig = create_sankey_diagram(filtered_summary)
            stats_table = create_stats_table(filtered_summary, filtered_detailed)
            duration_fig = create_duration_analysis(filtered_summary)
            category_fig = create_category_distribution(filtered_detailed)
            sequence_fig = create_sequence_analysis(filtered_summary)
            temporal_fig = create_temporal_patterns(filtered_summary)
            
            return sankey_fig, stats_table, duration_fig, category_fig, sequence_fig, temporal_fig
            
        except Exception as e:
            print(f"Error updating graphs: {str(e)}")
            return [go.Figure().to_dict() for _ in range(5)] + [html.Div("Error loading data")]
    
    return app

def create_sankey_diagram(filtered_summary):
    """Create enhanced Sankey diagram with better grouping and filtering"""
    if filtered_summary.empty:
        return go.Figure().to_dict()
    
    nodes = set()
    links = []
    
    # Clinical regimen mapping
    def standardize_regimen(regimen):
        if pd.isna(regimen):
            return "Unknown"
        regimen = regimen.lower()
        # Standard combination mappings
        if 'capecitabine' in regimen and 'oxaliplatin' in regimen:
            return 'CAPOX'
        if 'fluorouracil' in regimen and 'leucovorin' in regimen:
            if 'oxaliplatin' in regimen:
                return 'FOLFOX'
            if 'irinotecan' in regimen:
                return 'FOLFIRI'
        if 'bevacizumab' in regimen:
            if 'folfox' in regimen or ('fluorouracil' in regimen and 'oxaliplatin' in regimen):
                return 'FOLFOX + Bevacizumab'
            if 'folfiri' in regimen or ('fluorouracil' in regimen and 'irinotecan' in regimen):
                return 'FOLFIRI + Bevacizumab'
        if 'cetuximab' in regimen:
            if 'irinotecan' in regimen:
                return 'FOLFIRI + Cetuximab'
            return 'Cetuximab-based'
        return regimen.title()
    
    # Add treatment lines as nodes
    max_line = filtered_summary.line_of_therapy.max()
    for line in range(1, max_line + 1):
        nodes.add(f"Line {line}")
    
    # Process treatment patterns
    for pid in filtered_summary.patientid.unique():
        patient_lines = filtered_summary[filtered_summary.patientid == pid].sort_values('line_of_therapy')
        prev_line = None
        
        for i, row in patient_lines.iterrows():
            regimen = standardize_regimen(row.initial_regimen)
            current_line = f"Line {row.line_of_therapy}"
            
            # Ensure sequential progression
            if prev_line and int(current_line.split()[-1]) > int(prev_line.split()[-1]) + 1:
                continue  # Skip non-sequential progressions
                
            nodes.add(regimen)
            links.append((current_line, regimen, 1))
            
            if i < len(patient_lines) - 1:
                next_line = f"Line {patient_lines.iloc[i+1].line_of_therapy}"
                if int(next_line.split()[-1]) == int(current_line.split()[-1]) + 1:  # Ensure sequential
                    links.append((regimen, next_line, 1))
            
            prev_line = current_line
    
    # Convert nodes to list with specific ordering
    line_nodes = sorted([n for n in nodes if "Line" in n])
    regimen_nodes = sorted([n for n in nodes if "Line" not in n])
    nodes = line_nodes + regimen_nodes
    node_indices = {node: i for i, node in enumerate(nodes)}
    
    # Aggregate link values
    link_dict = {}
    for source, target, value in links:
        key = (node_indices[source], node_indices[target])
        link_dict[key] = link_dict.get(key, 0) + value
    
    # Calculate node positions
    num_lines = len(line_nodes)
    x_spacing = 0.8 / (num_lines - 1) if num_lines > 1 else 0.4
    
    # Create Sankey diagram with enhanced styling
    fig = go.Figure(data=[go.Sankey(
        node = dict(
            pad = 15,
            thickness = 20,
            line = dict(color = "black", width = 0.5),
            label = nodes,
            color = ["#1f77b4" if "Line" in n else "#2ecc71" for n in nodes],
            x = [0.1 + i * x_spacing if "Line" in n else None for i, n in enumerate(nodes)],
            y = [0.5 if "Line" in n else None for n in nodes]
        ),
        link = dict(
            source = [k[0] for k in link_dict.keys()],
            target = [k[1] for k in link_dict.keys()],
            value = list(link_dict.values()),
            color = ["rgba(169, 169, 169, 0.3)"]*len(link_dict)
        )
    )])
    
    fig.update_layout(
        title={
            'text': "Treatment Pattern Flow in mCRC",
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        font_size=12,
        height=600,
        width=1200,  # Increased width for better spacing
        paper_bgcolor='white',
        plot_bgcolor='white'
    )
    
    return fig.to_dict()  # Convert to dictionary for JSON serialization

def create_stats_table(filtered_summary, filtered_detailed):
    """Create summary statistics table with clinical context"""
    if filtered_summary.empty or filtered_detailed.empty:
        return html.Div("No data available")
    
    # Calculate advanced metrics
    total_patients = filtered_detailed.patientid.nunique()
    avg_lines = filtered_summary.groupby('patientid')['line_of_therapy'].max().mean()
    median_duration = filtered_summary['duration_days'].median()
    
    # Calculate progression rates
    progression_to_next = sum(filtered_summary.groupby('patientid')['line_of_therapy'].max() > 1) / total_patients * 100
    
    stats = html.Table([
        html.Tr([html.Th("Clinical Metric", style={'textAlign': 'left'}), 
                html.Th("Value", style={'textAlign': 'right'})],
               style={'backgroundColor': '#f8f9fa'}),
        html.Tr([
            html.Td("Total Patients", style={'fontWeight': 'bold'}),
            html.Td(f"{total_patients:,}", style={'textAlign': 'right'})
        ]),
        html.Tr([
            html.Td("Average Lines of Therapy", style={'fontWeight': 'bold'}),
            html.Td(f"{avg_lines:.1f}", style={'textAlign': 'right'})
        ]),
        html.Tr([
            html.Td("Median Treatment Duration", style={'fontWeight': 'bold'}),
            html.Td(f"{median_duration:.0f} days", style={'textAlign': 'right'})
        ]),
        html.Tr([
            html.Td("Progression to Next Line", style={'fontWeight': 'bold'}),
            html.Td(f"{progression_to_next:.1f}%", style={'textAlign': 'right'})
        ]),
        html.Tr([
            html.Td("Most Common Regimen", style={'fontWeight': 'bold'}),
            html.Td(f"{filtered_summary['initial_regimen'].mode().iloc[0]}", 
                   style={'textAlign': 'right'})
        ])
    ], style={'width': '100%', 'border': '1px solid #dee2e6'})
    
    return stats

def create_duration_analysis(filtered_summary):
    """Create enhanced box plot for treatment duration analysis"""
    if filtered_summary.empty:
        return go.Figure().to_dict()
    
    # Ensure line_of_therapy is treated as a category
    filtered_summary = filtered_summary.copy()
    filtered_summary['line_of_therapy'] = filtered_summary['line_of_therapy'].astype(str).map(lambda x: f'Line {x}')
    
    # Create box plot
    fig = go.Figure()
    
    # Get unique regimens for consistent colors
    regimens = sorted(filtered_summary['initial_regimen'].unique())
    
    # Define colors with both solid and transparent versions
    colors = [
        {'solid': '#FF9999', 'transparent': 'rgba(255,153,153,0.6)'},
        {'solid': '#66B2FF', 'transparent': 'rgba(102,178,255,0.6)'},
        {'solid': '#99FF99', 'transparent': 'rgba(153,255,153,0.6)'},
        {'solid': '#FFCC99', 'transparent': 'rgba(255,204,153,0.6)'},
        {'solid': '#FF99CC', 'transparent': 'rgba(255,153,204,0.6)'},
        {'solid': '#99FFCC', 'transparent': 'rgba(153,255,204,0.6)'},
        {'solid': '#FFB366', 'transparent': 'rgba(255,179,102,0.6)'},
        {'solid': '#FF99FF', 'transparent': 'rgba(255,153,255,0.6)'}
    ]
    
    # Ensure we have enough colors
    while len(colors) < len(regimens):
        colors.extend(colors)
    regimen_colors = dict(zip(regimens, colors[:len(regimens)]))
    
    # Add box plots for each regimen
    for regimen in regimens:
        mask = filtered_summary['initial_regimen'] == regimen
        color_dict = regimen_colors[regimen]
        
        fig.add_trace(go.Box(
            x=filtered_summary[mask]['line_of_therapy'],
            y=filtered_summary[mask]['duration_days'],
            name=regimen,
            boxmean=True,  # Add mean line
            marker_color=color_dict['solid'],
            line=dict(width=2),  # Make box lines thicker
            fillcolor=color_dict['transparent'],  # Semi-transparent version
            opacity=0.8
        ))
    
    # Update layout
    fig.update_layout(
        title='Treatment Duration by Line and Regimen',
        xaxis_title='Line of Therapy',
        yaxis_title='Duration (Days)',
        showlegend=True,
        height=600,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.02,
            bgcolor='rgba(255, 255, 255, 0.8)'
        ),
        paper_bgcolor='white',
        plot_bgcolor='white',
        boxmode='group',
        xaxis=dict(
            title_font=dict(size=14),
            tickfont=dict(size=12),
            gridcolor='lightgray',
            categoryorder='array',
            categoryarray=[f'Line {i}' for i in range(1, filtered_summary['line_of_therapy'].nunique() + 1)]
        ),
        yaxis=dict(
            title_font=dict(size=14),
            tickfont=dict(size=12),
            gridcolor='lightgray',
            zeroline=True,
            zerolinecolor='lightgray'
        ),
        margin=dict(l=50, r=150, t=50, b=50)  # Adjust margins to accommodate legend
    )
    
    return fig.to_dict()  # Convert to dictionary for JSON serialization

def create_category_distribution(filtered_detailed):
    """Create enhanced heatmap for drug category distribution"""
    if filtered_detailed.empty:
        return go.Figure().to_dict()
    
    category_dist = filtered_detailed.groupby(
        ['line_of_therapy', 'drug_class']
    ).size().unstack(fill_value=0)
    
    # Convert to percentages
    category_dist = category_dist.div(category_dist.sum(axis=1), axis=0) * 100
    
    fig = px.imshow(
        category_dist,
        labels=dict(
            x='Drug Category',
            y='Line of Therapy',
            color='Percentage of Patients'
        ),
        title='Drug Category Distribution by Line of Therapy',
        color_continuous_scale='RdYlBu_r'
    )
    
    fig.update_layout(
        height=400,
        xaxis_tickangle=-45,
        paper_bgcolor='white',
        plot_bgcolor='white'
    )
    
    return fig.to_dict()  # Convert to dictionary for JSON serialization

def create_sequence_analysis(filtered_summary):
    """Create enhanced visualization for treatment sequences"""
    if filtered_summary.empty:
        return go.Figure().to_dict()
    
    # Get top sequences
    sequences = defaultdict(int)
    for pid in filtered_summary.patientid.unique():
        patient_seq = filtered_summary[filtered_summary.patientid == pid].sort_values('line_of_therapy')
        seq = " → ".join(patient_seq.initial_regimen.values)
        sequences[seq] += 1
    
    # Convert to DataFrame and get top 10
    seq_df = pd.DataFrame(
        [(seq, count) for seq, count in sequences.items()],
        columns=['Sequence', 'Count']
    ).nlargest(10, 'Count')
    
    # Calculate percentages
    total_patients = filtered_summary.patientid.nunique()
    seq_df['Percentage'] = (seq_df['Count'] / total_patients * 100).round(1)
    
    fig = px.bar(
        seq_df,
        x='Percentage',
        y='Sequence',
        orientation='h',
        title='Most Common Treatment Sequences',
        labels={
            'Percentage': 'Percentage of Patients (%)',
            'Sequence': 'Treatment Sequence'
        }
    )
    
    fig.update_layout(
        height=400,
        paper_bgcolor='white',
        plot_bgcolor='white',
        yaxis={'categoryorder':'total ascending'}
    )
    
    return fig.to_dict()  # Convert to dictionary for JSON serialization

def create_temporal_patterns(filtered_summary):
    """Create temporal pattern analysis"""
    if filtered_summary.empty:
        return go.Figure()
    
    # Analyze regimen usage over time
    temporal = filtered_summary.groupby(
        ['year_quarter', 'initial_regimen']
    ).size().unstack(fill_value=0)
    
    # Convert to percentages
    temporal = temporal.div(temporal.sum(axis=1), axis=0) * 100
    
    # Sort by year_quarter
    temporal = temporal.sort_index()
    
    fig = px.line(
        temporal.reset_index().melt(id_vars=['year_quarter']),
        x='year_quarter',
        y='value',
        color='initial_regimen',
        title='Evolution of Treatment Patterns Over Time',
        labels={
            'year_quarter': 'Time Period',
            'value': 'Percentage of Patients (%)',
            'initial_regimen': 'Treatment Regimen'
        }
    )
    
    fig.update_layout(
        height=400,
        paper_bgcolor='white',
        plot_bgcolor='white',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.02
        ),
        xaxis_title="Time Period",
        yaxis_title="Percentage of Patients (%)"
    )
    
    # Add markers to the lines
    fig.update_traces(mode='lines+markers')
    
    return fig.to_dict()  # Convert to dictionary for JSON serialization

if __name__ == "__main__":
    try:
        # Read data efficiently with correct data types
        dtypes = {
            'patientid': 'int32',
            'line_of_therapy': 'int8',
            'duration_days': 'float32',
            'drugname': 'str',
            'drugcategory': 'str',
            'regimen': 'str',
            'regimen_status': 'str',
            'regimen_type': 'str',
            'maintenance_flag': 'bool'
        }
        
        # Define date columns for each file
        detailed_dates = ['administratedate', 'line_start_date', 'line_end_date']
        summary_dates = ['line_start_date', 'line_end_date']
        
        # Read detailed data
        detailed_df = pd.read_csv(
            'output/crc_lot_detailed.csv',
            dtype=dtypes,
            parse_dates=detailed_dates
        )
        
        # Read summary data
        summary_df = pd.read_csv(
            'output/crc_lot_summary.csv',
            dtype={col: dtypes[col] for col in dtypes if col in ['patientid', 'line_of_therapy', 'duration_days']},
            parse_dates=summary_dates
        )
        
        print(f"Loaded data successfully:")
        print(f"Detailed records: {len(detailed_df)}")
        print(f"Summary records: {len(summary_df)}")
        print(f"Total patients: {detailed_df.patientid.nunique()}")
        
        # Create and run dashboard
        app = create_dashboard(detailed_df, summary_df)
        app.run_server(debug=True, port=8050)
        
    except Exception as e:
        print(f"Error starting dashboard: {str(e)}")
        # Print more detailed error information
        import traceback
        traceback.print_exc()