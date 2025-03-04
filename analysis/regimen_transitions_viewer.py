import os
import pandas as pd
import plotly.graph_objects as go

def compute_transitions(data):
    """
    Compute valid regimen transitions for each patient (only consecutive lines).
    """
    transitions = []
    for patientid, group in data.groupby('patientid'):
        group = group.sort_values('line_of_therapy')
        lines = group[['line_of_therapy', 'regimen_type']].drop_duplicates()
        lines = lines.reset_index(drop=True)
        
        if len(lines) < 2:
            continue
            
        # Only consider consecutive line transitions (1L->2L, 2L->3L, etc.)
        for i in range(len(lines) - 1):
            curr_line = lines.loc[i, 'line_of_therapy']
            next_line = lines.loc[i+1, 'line_of_therapy']
            
            # Skip if lines are not consecutive
            if next_line != curr_line + 1:
                continue
                
            transition = f"{curr_line}L -> {next_line}L"
            transitions.append({
                'patientid': patientid,
                'transition': transition,
                'init_regimen': lines.loc[i, 'regimen_type'],
                'next_regimen': lines.loc[i+1, 'regimen_type']
            })
    return pd.DataFrame(transitions)

def aggregate_transitions(transitions_df):
    """
    Aggregate counts and calculate percentages for each transition pattern.
    """
    # Count transitions
    agg = transitions_df.groupby(['transition', 'init_regimen', 'next_regimen']).size().reset_index(name='count')
    
    # Calculate percentages within each initial regimen group
    agg['percentage'] = agg.groupby(['transition', 'init_regimen'])['count'].transform(
        lambda x: (x / x.sum()) * 100
    )
    return agg

def filter_top3(agg_df, transition_filter):
    """
    First get top 3 initial regimens by total count, then for each of those,
    get their top 3 next regimens by percentage.
    """
    subset = agg_df[agg_df['transition'] == transition_filter]
    if subset.empty:
        return pd.DataFrame()
        
    # Get total counts for each initial regimen
    init_reg_counts = subset.groupby('init_regimen')['count'].sum().sort_values(ascending=False)
    top_init_regimens = init_reg_counts.head(3).index.tolist()
    
    # Filter for top 3 initial regimens and their top 3 next regimens
    top_rows = []
    for init_regimen in top_init_regimens:
        group = subset[subset['init_regimen'] == init_regimen]
        top_group = group.nlargest(3, 'percentage')
        top_rows.append(top_group)
    
    return pd.concat(top_rows) if top_rows else pd.DataFrame()

def create_figure(agg_df, available_transitions):
    """
    Create horizontal bar chart with dropdown menu for transition types.
    Modified to update traces via visibility.
    """
    all_traces = []
    group_indices = {}  # mapping from transition to its trace indices
    trace_count = 0
    for t in available_transitions:
        filtered = filter_top3(agg_df, t)
        if filtered.empty:
            group_indices[t] = []
            continue
        init_regs = sorted(filtered['init_regimen'].unique())
        group = []
        for ir in init_regs:
            sub_data = filtered[filtered['init_regimen'] == ir]
            percentages = sub_data['percentage'].values
            counts = sub_data['count'].values
            next_regimens = sub_data['next_regimen'].values
            trace = go.Bar(
                x=percentages,
                y=[ir] * len(percentages),
                orientation='h',
                text=[f"{nr}<br>{p:.1f}% (n={c})" for nr, p, c in zip(next_regimens, percentages, counts)],
                textposition='auto',
                showlegend=False,
                marker_color=['#1f77b4', '#ff7f0e', '#2ca02c'][:len(percentages)],
                hovertemplate="<b>From:</b> %{y}<br>" +
                              "<b>To:</b> %{text}<br>" +
                              "<extra></extra>"
            )
            all_traces.append(trace)
            group.append(trace_count)
            trace_count += 1
        group_indices[t] = group

    default_transition = next((t for t in available_transitions if group_indices[t]), available_transitions[0])
    default_visibility = [False] * len(all_traces)
    for i in group_indices[default_transition]:
        default_visibility[i] = True

    # Set each trace's initial visibility
    for idx, trace in enumerate(all_traces):
        trace.visible = default_visibility[idx]

    layout = go.Layout(
        title=f"Top 3 Next-Line Regimens: {default_transition}",
        barmode='group',
        yaxis=dict(
            title="Initial Regimen (Top 3 by Patient Count)",
            automargin=True
        ),
        xaxis=dict(
            title="Percentage of Patients (%)",
            range=[0, 100]
        ),
        margin=dict(l=200, r=50, t=100, b=50),
        showlegend=False,
        height=400,
        updatemenus=[dict(
            type="dropdown",
            direction="down",
            x=0.5,
            y=1.15,
            xanchor='center',
            yanchor='top',
            showactive=True,
            active=0,
            buttons=[
                {
                    "label": t,
                    "method": "update",
                    "args": [
                        {"visible": [i in group_indices[t] for i in range(len(all_traces))]},
                        {"title": f"Top 3 Next-Line Regimens: {t}"}
                    ]
                } for t in available_transitions if group_indices[t]
            ]
        )],
        annotations=[dict(
            text="Select Transition Type:",
            x=0.5,
            y=1.22,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=14)
        )]
    )
    fig = go.Figure(data=all_traces, layout=layout)
    return fig

def main():
    """
    Main execution function to load data and create the visualization.
    """
    # Load the CSV file (update path if needed)
    file_path = "output/crc_lot_detailed.csv"
    try:
        data = pd.read_csv(file_path)
        print("Data loaded successfully!")
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return

    # Ensure required columns exist
    required_columns = ['patientid', 'line_of_therapy', 'regimen_type']
    for column in required_columns:
        if column not in data.columns:
            print(f"Missing required column: {column}")
            return

    # Compute and aggregate transitions
    transitions_df = compute_transitions(data)
    if transitions_df.empty:
        print("No valid transitions found in data.")
        return

    agg_df = aggregate_transitions(transitions_df)
    available_transitions = sorted(agg_df['transition'].unique())
    print(f"Available transitions: {available_transitions}")

    # Create and save the interactive visualization
    fig = create_figure(agg_df, available_transitions)
    
    # Create output directory if it doesn't exist
    output_dir = "regimen_transition_plots"
    os.makedirs(output_dir, exist_ok=True)
    
    # Save the interactive HTML file
    output_file = os.path.join(output_dir, "regimen_transitions.html")
    fig.write_html(output_file)
    print(f"Interactive visualization saved to: {output_file}")
    
    # Display the figure in the browser
    fig.show()

if __name__ == "__main__":
    main()