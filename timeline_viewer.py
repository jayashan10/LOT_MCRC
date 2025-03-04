import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import os

class TimelineViewer:
    def __init__(self, detailed_output_df, summary_output_df=None):
        """Initialize the timeline viewer with detailed and summary output dataframes"""
        self.detailed_df = detailed_output_df
        self.summary_df = summary_output_df
        self.output_dir = "timeline_outputs"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Define source-specific markers with descriptive names
        self.source_markers = {
            'ORDER': 'circle',
            'ADMIN': 'diamond',
            'UNSTRUCTURED': 'star'
        }
        
        # Define a color palette for lines and drugs
        self.line_colors = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]
        
    def view_patient_timeline(self, patient_id):
        """
        Generate and display an interactive timeline for a specific patient,
        including details from the summary lines.
        """
        patient_df = self.detailed_df[self.detailed_df['patientid'] == patient_id].copy()
        if patient_df.empty:                                                                                                                                                                                                                                                                                                                                                                                                                        
            print(f"No data found for patient {patient_id}")
            return None
        
        patient_summary = None
        if self.summary_df is not None:
            patient_summary = self.summary_df[self.summary_df['patientid'] == patient_id].copy()
        
        fig = self._create_timeline_figure(patient_df, patient_summary)
        output_file = os.path.join(self.output_dir, f'patient_{patient_id}_timeline.html')
        fig.write_html(output_file)
        
        print(f"Timeline created: {output_file}")
        return output_file
    
    def _create_timeline_figure(self, patient_df, patient_summary):
        # Create subplots
        fig = make_subplots(
            rows=3, cols=1,
            row_heights=[0.45, 0.25, 0.3],
            specs=[[{"type": "xy"}], [{"type": "xy"}], [{"type": "domain"}]],
            subplot_titles=("Treatment Timeline", "Drug Exposure Pattern", "Summary Details"),
            vertical_spacing=0.08
        )
        
        # Prepare trace info for filter buttons (for actual data traces only)
        trace_info = []
        unique_lines = sorted(patient_df['line_of_therapy'].unique())
        unique_drugs = sorted(patient_df['drugname'].unique())
        
        # --- Treatment Timeline Data: Group by line and source (data traces) ---
        for line_num in unique_lines:
            line_color = self.line_colors[unique_lines.index(line_num) % len(self.line_colors)]
            line_df = patient_df[patient_df['line_of_therapy'] == line_num]
            for source, group in line_df.groupby('SOURCE'):
                trace = go.Scatter(
                    x=group['administratedate'],
                    y=[line_num] * len(group),
                    mode='markers+text',
                    text=group['drugname'],
                    textposition="top center",
                    marker=dict(
                        symbol=self.source_markers.get(source, 'circle'),
                        size=12,
                        color=line_color
                    ),
                    name=f"Line {line_num} ({source})",
                    hovertemplate=(
                        '<b>Drug:</b> %{text}<br>' +
                        '<b>Date:</b> %{x}<br>' +
                        '<b>Line:</b> %{y}<br>' +
                        '<b>Source:</b> ' + source + '<br>' +
                        '<b>Regimen:</b> %{customdata}<br>' +
                        '<extra></extra>'
                    ),
                    customdata=group['regimen_type'],
                    showlegend=False  # Hide from legend; dummy used instead
                )
                fig.add_trace(trace, row=1, col=1)
                trace_info.append({'source': source})
        
        # --- Drug Exposure Data: Group by drug and source (data traces) ---
        for drug in unique_drugs:
            drug_data = patient_df[patient_df['drugname'] == drug]
            drug_color = self.line_colors[unique_drugs.index(drug) % len(self.line_colors)]
            for source, group in drug_data.groupby('SOURCE'):
                y_val = unique_drugs.index(drug)
                trace = go.Scatter(
                    x=group['administratedate'],
                    y=[y_val] * len(group),
                    mode='markers',
                    marker=dict(
                        symbol=self.source_markers.get(source, 'circle'),
                        size=8,
                        color=drug_color
                    ),
                    name=f"{drug} ({source})",
                    hovertemplate=(
                        f'<b>{drug}</b><br>' +
                        'Date: %{x}<br>' +
                        '<b>Source:</b> ' + source + '<br>' +
                        '<b>Line:</b> %{customdata}<br>' +
                        '<extra></extra>'
                    ),
                    customdata=group['line_of_therapy'],
                    showlegend=False  # Hide from legend; dummy used instead
                )
                fig.add_trace(trace, row=2, col=1)
                trace_info.append({'source': source})
        
        # Update y-axis for drug exposure panel
        fig.update_yaxes(
            ticktext=unique_drugs,
            tickvals=list(range(len(unique_drugs))),
            row=2, col=1
        )
        
        # --- Add Summary Table if available ---
        if patient_summary is not None and not patient_summary.empty:
            # ...existing code to format dates...
            if pd.api.types.is_datetime64_any_dtype(patient_summary['line_start_date']):
                patient_summary['line_start_date'] = patient_summary['line_start_date'].dt.strftime('%Y-%m-%d')
            if pd.api.types.is_datetime64_any_dtype(patient_summary['line_end_date']):
                patient_summary['line_end_date'] = patient_summary['line_end_date'].dt.strftime('%Y-%m-%d')
            table_trace = go.Table(
                header=dict(
                    values=["Line", "Start Date", "End Date", "Duration", "Drugs (Admin Count)", "Regimen Type"],
                    fill_color='paleturquoise',
                    align='center',
                    font=dict(size=12, color='black')
                ),
                cells=dict(
                    values=[
                        patient_summary['line_of_therapy'],
                        patient_summary['line_start_date'],
                        patient_summary['line_end_date'],
                        patient_summary['duration_days'],
                        patient_summary['drug_admin_counts'],
                        patient_summary['regimen_type']
                    ],
                    fill_color='lavender',
                    align=['center', 'center', 'center', 'center', 'left', 'center'],
                    font=dict(size=11)
                )
            )
            fig.add_trace(table_trace, row=3, col=1)
            trace_info.append({'type': 'table'})
        
        # --- Append Dummy Legend Traces (static legends) ---
        # Dummy traces for Lines of therapies
        for idx, line_num in enumerate(unique_lines):
            line_color = self.line_colors[idx % len(self.line_colors)]
            dummy = go.Scatter(
                x=[None],
                y=[None],
                mode='markers',
                marker=dict(color=line_color, size=12),
                name=f"Line {line_num}",
                legendgroup="lines",
                showlegend=True
            )
            if idx == 0:
                dummy.legendgrouptitle = dict(text="Line of therapies:")
            fig.add_trace(dummy, row=1, col=1)
            trace_info.append({'dummy': True})
        
        # Dummy traces for Data Sources
        for idx, source in enumerate(self.source_markers.keys()):
            dummy = go.Scatter(
                x=[None],
                y=[None],
                mode='markers',
                marker=dict(symbol=self.source_markers[source], color='gray', size=12),
                name=source,
                legendgroup="sources",
                showlegend=True
            )
            if idx == 0:
                dummy.legendgrouptitle = dict(text="Data Sources:")
            fig.add_trace(dummy, row=1, col=1)
            trace_info.append({'dummy': True})
        
        # Dummy traces for Drugs
        for idx, drug in enumerate(unique_drugs):
            drug_color = self.line_colors[unique_drugs.index(drug) % len(self.line_colors)]
            dummy = go.Scatter(
                x=[None],
                y=[None],
                mode='markers',
                marker=dict(color=drug_color, size=8),
                name=drug,
                legendgroup="drugs",
                showlegend=True
            )
            if idx == 0:
                dummy.legendgrouptitle = dict(text="Drugs:")
            fig.add_trace(dummy, row=2, col=1)
            trace_info.append({'dummy': True})
        
        # --- Create Filter Buttons based on source (toggles actual data traces only) ---
        buttons = []
        # "All Sources" button: show all traces (dummy and data, but table always visible)
        buttons.append(dict(
            label="All Sources",
            method="update",
            args=[{"visible": [True] * len(fig.data)}]
        ))
        # One button per source
        for source in self.source_markers:
            visibility = []
            for i in range(len(fig.data)):
                info = trace_info[i] if i < len(trace_info) else {}
                # Always show dummy and table traces
                if info.get('dummy', False) or info.get('type') == 'table':
                    visibility.append(True)
                else:
                    visibility.append(info.get('source') == source)
            buttons.append(dict(
                label=source,
                method="update",
                args=[{"visible": visibility}]
            ))
        # New Combined Filter: "Order + Admin"
        combined_visibility = []
        for i in range(len(fig.data)):
            info = trace_info[i] if i < len(trace_info) else {}
            if info.get('dummy', False) or info.get('type') == 'table':
                combined_visibility.append(True)
            else:
                combined_visibility.append(info.get('source') in ['ORDER', 'ADMIN'])
        buttons.append(dict(
            label="Order + Admin",
            method="update",
            args=[{"visible": combined_visibility}]
        ))
        
        fig.update_layout(
            title=f"Treatment Timeline for Patient {patient_df['patientid'].iloc[0]}",
            showlegend=True,
            height=1000,
            width=1200,
            legend=dict(
                groupclick="toggleitem",
                itemclick="toggle",
                traceorder="grouped"
            ),
            margin=dict(t=150, b=50, l=50, r=50),
            updatemenus=[dict(
                type="buttons",
                direction="right",
                active=0,
                x=0.5,
                y=1.15,
                xanchor='center',
                buttons=buttons
            )],
            annotations=[dict(
                x=0.5,
                y=1.12,
                xref="paper",
                yref="paper",
                text="Filter by Source:",
                showarrow=False,
                font=dict(size=14)
            )]
        )
        
        return fig