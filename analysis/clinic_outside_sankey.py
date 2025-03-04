import pandas as pd
import os
import plotly.graph_objects as go

def create_improved_sankey(detailed_df, summary_df, output_file='analysis/figures/improved_sankey.html'):
    """
    Create a Sankey diagram in the style of the example image, showing patient flow
    through different lines of therapy with percentages and counts displayed.
    Shows a simple flow from Start → 1L → 2L → 3L with branches for discontinuation.
    """
    # Identify all unique line numbers
    all_lines = sorted(summary_df['line_of_therapy'].unique())
    max_line = max(all_lines)
    print(max_line)
    # Count total patients
    total_patients = summary_df['patientid'].nunique()
    
    # Get patient counts per line of therapy
    line_patients = {}
    for line in all_lines:
        line_patients[line] = summary_df[summary_df['line_of_therapy'] == line]['patientid'].nunique()
    
    # Build transitions with simple flow
    transitions = []
    
    # Add Start to Line 1 transition
    l1_patients = line_patients.get(1, 0)
    transitions.append({
        'source': 'Start',
        'target': '1L',
        'count': l1_patients,
        'percentage': 100.0
    })
    
    # For each line transition
    for i in range(1, max_line):
        current_line = i
        next_line = i + 1
        
        # Get patients in current and next line
        current_patients = line_patients.get(current_line, 0)
        next_patients = line_patients.get(next_line, 0)
        
        # Count patients who progress from current to next line
        patients_continuing = 0
        for patient, group in summary_df.groupby('patientid'):
            lines = group['line_of_therapy'].tolist()
            if current_line in lines and next_line in lines:
                patients_continuing += 1
        
        # Calculate percentage that continues to next line
        if current_patients > 0:
            continue_percentage = (patients_continuing / current_patients) * 100
        else:
            continue_percentage = 0
            
        # Calculate patients who discontinue
        discontinue_patients = current_patients - patients_continuing
        if current_patients > 0:
            discontinue_percentage = (discontinue_patients / current_patients) * 100
        else:
            discontinue_percentage = 0
            
        # Add transition to next line
        if patients_continuing > 0:
            transitions.append({
                'source': f'{current_line}L',
                'target': f'{next_line}L',
                'count': patients_continuing,
                'percentage': continue_percentage
            })
            
        # Add transition to discontinuation
        if discontinue_patients > 0:
            transitions.append({
                'source': f'{current_line}L',
                'target': f'End {current_line}',
                'count': discontinue_patients,
                'percentage': discontinue_percentage
            })
    
    # Build unique node list
    all_nodes = []
    for t in transitions:
        if t['source'] not in all_nodes:
            all_nodes.append(t['source'])
        if t['target'] not in all_nodes:
            all_nodes.append(t['target'])
    
    # Create node positioning - improved for better layout
    node_x = []
    node_y = []
    node_colors = []
    node_labels = []
    
    # Space constants for better positioning
    horizontal_spacing = 0.9 / (max_line + 1)  # Further reduced spacing
    vertical_offset = 0.2
    
    for node in all_nodes:
        if node == 'Start':
            node_x.append(0.02)  # Even smaller start
            node_y.append(0.5)  # Center vertically
            node_colors.append('#8B0000')  # Darker node color for Start
            node_labels.append(f"mCRC<br>(N={total_patients})")
            
        elif node.startswith('L'):  # Line nodes (L1, L2, L3)
            # Extract line number
            line_num = int(''.join(filter(str.isdigit, node)))  # Extract line number from node label
            # Adjust x-position for the last line to ensure it's on the right
            if line_num == max_line:
                node_x.append(0.02 + line_num * horizontal_spacing + horizontal_spacing * 0.2)  # Push last line label right
            else:
                node_x.append(0.02 + line_num * horizontal_spacing)  # Normal positioning for other lines
            node_y.append(0.5)  # Center vertically
            node_colors.append('#8B0000')  # Darker node color for Line nodes
            
            # Create label with count/percentage
            count = line_patients.get(line_num, 0)
            percentage = (count / total_patients) * 100
            node_labels.append(f"{line_num}L<br>{percentage:.0f}%<br>({count}/{total_patients})")
            
        elif node.startswith('End'):  # End/terminal nodes
            # Extract the line number it's coming from
            line_num = int(''.join(filter(str.isdigit, node)))  # Extract line number from node label
            
            # Position to the right of source with better spacing
            # Stagger end nodes to avoid overlapping
            node_x.append(0.02 + line_num * horizontal_spacing + horizontal_spacing * 0.4)  # Adjust end node offset
            # Position below for discontinuation flows
            node_y.append(0.15)
            node_colors.append('#00008B')  # Darker node color for End nodes
            
            # Find the transition that targets this node to get the count and percentage
            count = 0
            percentage = 0
            for t in transitions:
                if t['target'] == node:
                    count = t['count']
                    percentage = t['percentage']
                    break
            
            # Find source line count for denominator
            source_count = line_patients.get(line_num, 0)
            node_labels.append(f"{percentage:.0f}%<br>({count}/{source_count})")
    
    # Map node names to indices
    node_indices = {name: i for i, name in enumerate(all_nodes)}
    
    # Prepare sankey link data
    link_source = []
    link_target = []
    link_value = []
    link_colors = []
    
    for t in transitions:
        src = t['source']
        tgt = t['target']
        count = t['count']
        
        link_source.append(node_indices[src])
        link_target.append(node_indices[tgt])
        link_value.append(count)
        
        # Color links based on source/target
        if tgt.startswith('End'):
            link_colors.append('#87CEFA')  # Lighter link color for discontinuation flows
        else:
            link_colors.append('#FF7F7F')  # Lighter link color for main flow
    
    # Create the Sankey diagram with proper styling to match example
    fig = go.Figure(data=[go.Sankey(
        arrangement="fixed",  # Use fixed positioning instead of snap
        node=dict(
            pad=15,           # Reduced padding for tighter layout
            thickness=20,     # Adjusted thickness to match example
            line=dict(color="black", width=0.5),
            label=node_labels,
            color=node_colors,
            x=node_x,
            y=node_y,
            customdata=node_labels,  # Store labels for hover
            hovertemplate='%{customdata}<extra></extra>',
        ),
        link=dict(
            source=link_source,
            target=link_target,
            value=link_value,
            color=link_colors
        )
    )])
    
    # Update layout with more specific styling to match example
    fig.update_layout(
        title_text="Patient Treatment Flow by Line of Therapy",
        font_size=14,
        width=1600,  # Increased width
        height=800,
        plot_bgcolor='white',
        margin=dict(l=100, r=100, t=50, b=25),  # Increased left and right margins
        title_font=dict(size=18),
        # Disable hover mode to prevent hover effects from blocking view
        hovermode='closest'
    )
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    fig.write_html(output_file)
    print(f"Improved Sankey diagram saved to: {output_file}")
    return fig

def create_clinic_outside_sankey(detailed_df, summary_df, output_file='analysis/figures/clinic_outside_sankey.html'):
    """
    Create a Sankey diagram showing patient flow through lines of therapy,
    split by whether the treatment was within the clinic or outside (based on
    the presence of unstructured data).
    """
    # Identify all unique line numbers
    all_lines = sorted(summary_df['line_of_therapy'].unique())
    max_line = max(all_lines)
    
    # Count total patients
    total_patients = summary_df['patientid'].nunique()
    
    # Get patient counts per line of therapy
    line_patients = {}
    for line in all_lines:
        line_patients[line] = summary_df[summary_df['line_of_therapy'] == line]['patientid'].nunique()
    
    # Determine treatment location for each line of therapy
    def determine_treatment_location(patient_id, line_number):
        """
        Determine if treatment was administered in clinic or outside based on SOURCE column.
        Returns 'Outside Clinic' if any treatment in the line has SOURCE='UNSTRUCTURED',
        otherwise returns 'Clinic'
        """
        line_data = detailed_df[(detailed_df['patientid'] == patient_id) & 
                              (detailed_df['line_of_therapy'] == line_number)]
        if any(line_data['SOURCE'] == 'UNSTRUCTURED'):
            return 'Outside Clinic'
        return 'Clinic'
    
    # Build transitions
    transitions = []
    
    # Add Start to Line 1 transition
    line1_patients = summary_df[summary_df['line_of_therapy'] == 1]['patientid'].unique()
    l1_patients = len(line1_patients)
    
    # Calculate clinic vs outside split for Line 1 based solely on unique patients
    l1_clinic = sum(1 for patient in line1_patients if determine_treatment_location(patient, 1) == 'Clinic')
    l1_outside = l1_patients - l1_clinic
    
    # Calculate percentages; these will add up to 100 (if l1_patients > 0)
    l1_clinic_percentage = (l1_clinic / l1_patients * 100) if l1_patients > 0 else 0
    l1_outside_percentage = (l1_outside / l1_patients * 100) if l1_patients > 0 else 0
    
    transitions.append({
        'source': 'Start',
        'target': 'L1',
        'count': l1_patients,
        'clinic_percentage': l1_clinic_percentage,
        'outside_percentage': l1_outside_percentage,
        'clinic_count': l1_clinic,
        'outside_count': l1_outside
    })

    # For each subsequent line transition
    for i in range(1, max_line):
        current_line = i
        next_line = i + 1

        current_patients = line_patients.get(current_line, 0)
        patients_continuing = 0
        clinic_cont = 0
        outside_cont = 0
        for patient, group in summary_df.groupby('patientid'):
            lines = group['line_of_therapy'].tolist()
            if current_line in lines and next_line in lines:
                patients_continuing += 1
                current_treatment = determine_treatment_location(patient, current_line)
                if current_treatment == 'Clinic':
                    clinic_cont += 1
                else:
                    outside_cont += 1

        if patients_continuing > 0:
            clinic_percentage = (clinic_cont / patients_continuing) * 100
            outside_percentage = (outside_cont / patients_continuing) * 100
        else:
            clinic_percentage = 0
            outside_percentage = 0

        if patients_continuing > 0:
            transitions.append({
                'source': f'L{current_line}',
                'target': f'L{next_line}',
                'count': patients_continuing,
                'clinic_percentage': clinic_percentage,
                'outside_percentage': outside_percentage,
                'percentage': (patients_continuing / current_patients * 100) if current_patients > 0 else 0,
                'clinic_count': clinic_cont,
                'outside_count': outside_cont
            })

        discontinue_patients = current_patients - patients_continuing
        if current_patients > 0:
            discontinue_percentage = (discontinue_patients / current_patients) * 100
        else:
            discontinue_percentage = 0

        if discontinue_patients > 0:
            transitions.append({
                'source': f'L{current_line}',
                'target': f'End{current_line}',
                'count': discontinue_patients,
                'clinic_percentage': 0,
                'outside_percentage': 0,
                'percentage': discontinue_percentage
            })

    # Build unique node list
    all_nodes = []
    for t in transitions:
        if t['source'] not in all_nodes:
            all_nodes.append(t['source'])
        if t['target'] not in all_nodes:
            all_nodes.append(t['target'])

    # Create node positioning
    node_x = []
    node_y = []
    node_colors = []
    node_labels = []

    # Space constants for better positioning
    horizontal_spacing = 0.9 / (max_line + 1)  # Further reduced spacing

    for node in all_nodes:
        if node == 'Start':
            node_x.append(0.02)
            node_y.append(0.5)
            node_colors.append('red')
            node_labels.append(f"mCRC<br>(N={total_patients})")

        elif node.startswith('L'):
            # Extract line number - Format is "L1", "L2", etc.
            line_num = int(node[1:])
            
            # Important: Force the last line to have more spacing
            if line_num == max_line:
                node_x.append(0.02 + line_num * horizontal_spacing + 0.1)  # Extra offset for last line
            else:
                node_x.append(0.02 + line_num * horizontal_spacing)
                
            node_y.append(0.5)
            count = line_patients.get(line_num, 0)
            percentage = (count / total_patients) * 100

            # Retrieve clinic/outside percentages and counts from transitions
            clinic_percentage = 0
            outside_percentage = 0
            clinic_count = 0
            outside_count = 0
            for t in transitions:
                if t['target'] == node:
                    clinic_percentage = t.get('clinic_percentage', 0)
                    outside_percentage = t.get('outside_percentage', 0)
                    clinic_count = t.get('clinic_count', 0)
                    outside_count = t.get('outside_count', 0)
                    break

            node_labels.append(
                f"<b>{line_num}L</b><br>" +
                f"Total: {percentage:.0f}% ({count}/{total_patients})<br>" +
                f"<span style='color:rgb(46,139,87)'>■</span> Clinic: {clinic_percentage:.0f}% ({clinic_count})<br>" +
                f"<span style='color:rgb(205,92,92)'>■</span> Outside: {outside_percentage:.0f}% ({outside_count})"
            )
            node_colors.append('#DCDCDC')

        elif node.startswith('End'):
            # Extract line number - Format is "End1", "End2", etc.
            line_num = int(node[3:])
            node_x.append(0.02 + line_num * horizontal_spacing + horizontal_spacing * 0.4)
            node_y.append(0.15)
            node_colors.append('blue')
            target_transition = next((t for t in transitions if t['target'] == node), None)
            count = target_transition['count'] if target_transition else 0
            percentage = target_transition['percentage'] if target_transition else 0
            source_count = line_patients.get(line_num, 0)
            node_labels.append(f"Discontinued<br>{percentage:.0f}%<br>({count}/{source_count})")

    # Map node names to indices
    node_indices = {name: i for i, name in enumerate(all_nodes)}

    # Prepare sankey link data
    link_source = []
    link_target = []
    link_value = []
    link_colors = []

    for t in transitions:
        src = t['source']
        tgt = t['target']
        count = t['count']

        link_source.append(node_indices[src])
        link_target.append(node_indices[tgt])
        link_value.append(count)

        # Color links based on source/target
        if tgt.startswith('End'):
            link_colors.append('#87CEFA')  # Lighter link color for discontinuation flows
        else:
            link_colors.append('#FF7F7F')  # Lighter link color for main flow

    # Create the Sankey diagram with proper styling to match example
    fig = go.Figure(data=[go.Sankey(
        arrangement="fixed",
        node=dict(
            pad=20,  # Increased padding for better label visibility
            thickness=25,  # Increased thickness for better visibility
            line=dict(color="black", width=0.5),
            label=node_labels,
            color=node_colors,
            x=node_x,
            y=node_y,
            customdata=node_labels,
            hovertemplate='%{customdata}<extra></extra>',
        ),
        link=dict(
            source=link_source,
            target=link_target,
            value=link_value,
            color=[
                '#87CEFA' if transitions[i]['target'].startswith('End') 
                else (
                    'rgba(46,139,87,0.6)' if transitions[i].get('clinic_percentage', 0) > transitions[i].get('outside_percentage', 0)
                    else 'rgba(205,92,92,0.6)'
                )
                for i in range(len(link_source))
            ]
        )
    )])

    # Add a legend
    fig.update_layout(
        annotations=[
            dict(
                x=1.02,
                y=0.95,
                xref="paper",
                yref="paper",
                text="<b>Treatment Location</b><br>" +
                     "<span style='color:rgb(46,139,87)'>■</span> Clinic<br>" +
                     "<span style='color:rgb(205,92,92)'>■</span> Outside Clinic<br>" +
                     "<span style='color:rgb(135,206,250)'>■</span> Discontinued",
                showarrow=False,
                bgcolor="white",
                bordercolor="black",
                borderwidth=1,
                borderpad=4
            )
        ],
        margin=dict(l=100, r=150, t=50, b=25),
        width=2000,   # Increased width for better label visibility
        height=1000   # Increased height as well
    )

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    fig.write_html(output_file)
    print(f"Clinic vs. Outside Sankey diagram saved to: {output_file}")
    return fig


# Example usage:
if __name__ == "__main__":
    # Read detailed and summary CSVs
    detailed_df = pd.read_csv('output/crc_lot_detailed.csv', parse_dates=['administratedate'])
    summary_df = pd.read_csv('output/crc_lot_summary.csv', parse_dates=['line_start_date', 'line_end_date'])
    
    create_improved_sankey(detailed_df, summary_df)
    create_clinic_outside_sankey(detailed_df, summary_df)