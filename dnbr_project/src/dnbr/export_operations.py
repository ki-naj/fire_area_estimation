import csv
from pathlib import Path
from datetime import datetime


def export_analysis_to_csv(analyses_dict, output_dir):

    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    summary_file = output_dir / "analysis_summary.csv"
    
    # Check if file exists and read existing data
    file_exists = summary_file.exists()
    existing_rows = []
    
    if file_exists:
        with open(summary_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            existing_rows = list(reader) if reader else []
    
    # Get today's date for duplicate detection
    today = datetime.now().date().isoformat()
    
    # Create a set of analysis names from today to avoid duplicates
    existing_analysis_today = {
        row['Analysis Name'] for row in existing_rows 
        if row.get('Timestamp', '').startswith(today)
    }
    
    # Filter out analyses that are being re-run today
    rows_to_keep = [
        row for row in existing_rows 
        if row['Analysis Name'] not in existing_analysis_today
    ]
    
    # Prepare new rows
    timestamp = datetime.now().isoformat()
    new_rows = []
    
    for key, result in analyses_dict.items():
        aoi_type = 'Original AOI' if 'Original AOI' in result['aoi_name'] else 'Bounding Box AOI'
        
        # Build base row with common fields
        row = {
            'Analysis Name': result['aoi_name'],
            'AOI Type': aoi_type,
            'Analysis Type': result['analysis_type'].upper(),
            'Water Masked': 'YES' if result['water_masked'] else 'NO',
            'AOI Area (ha)': f"{result['aoi_area']:.4f}",
            'Otsu Threshold': f"{result['otsu_threshold']:.4f}",
            'Otsu Area (ha)': f"{result['otsu_area']:.4f}",
            'Low (>0.05)': f"{result['threshold_areas'].get('low', 0):.4f}",
            'Moderate-Low (>0.075)': f"{result['threshold_areas'].get('moderate_low', 0):.4f}",
            'Moderate (>0.1)': f"{result['threshold_areas'].get('moderate', 0):.4f}",
            'High (>0.2)': f"{result['threshold_areas'].get('high', 0):.4f}",
            'Very High (>0.3)': f"{result['threshold_areas'].get('very_high', 0):.4f}",
            'Burned Area (ha)': f"{result['total_area']:.4f}",
            'Map File': result['map_file'].name,
            'Timestamp': timestamp
        }
        new_rows.append(row)
    
    # Combine kept rows with new rows
    all_rows = rows_to_keep + new_rows
    
    # Write all rows
    if all_rows:
        with open(summary_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'Analysis Name',
                'AOI Type',
                'Analysis Type',
                'Water Masked',
                'AOI Area (ha)',
                'Otsu Threshold',
                'Otsu Area (ha)',
                'Low (>0.05)',
                'Moderate-Low (>0.075)',
                'Moderate (>0.1)',
                'High (>0.2)',
                'Very High (>0.3)',
                'Burned Area (ha)',
                'Map File',
                'Timestamp'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            writer.writerows(all_rows)
    
    print(f"\n[CSV] Analysis summary exported: {summary_file}")
    print(f"[CSV] Total analyses in summary: {len(all_rows)}")
    
    return summary_file

def export_analysis_to_csv_10m(analyses_dict, output_dir):    
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    summary_file = output_dir / "analysis_summary_10m.csv"
    file_exists = summary_file.exists()
    existing_rows = []
    
    if file_exists:
        with open(summary_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            existing_rows = list(reader) if reader else []
    
    # Get today's date for duplicate detection
    today = datetime.now().date().isoformat()
    
    # Create a set of analysis names from today to avoid duplicates
    existing_analysis_today = {
        row['Analysis Name'] for row in existing_rows 
        if row.get('Timestamp', '').startswith(today)
    }
    
    # Filter out analyses that are being re-run today
    rows_to_keep = [
        row for row in existing_rows 
        if row['Analysis Name'] not in existing_analysis_today
    ]
    
    # Prepare new rows
    timestamp = datetime.now().isoformat()
    new_rows = []
    
    for key, result in analyses_dict.items():
        aoi_type = 'Original AOI' if 'Original AOI' in result['aoi_name'] else 'Bounding Box AOI'
        
        # Build base row with common fields
        row = {
            'Analysis Name': result['aoi_name'],
            'AOI Type': aoi_type,
            'Analysis Type': result['analysis_type'].upper(),
            'Water Masked': 'YES' if result['water_masked'] else 'NO',
            'Resolution': '10m',
            'AOI Area (ha)': f"{result['aoi_area']:.4f}",
            'Otsu Threshold': f"{result['otsu_threshold']:.4f}",
            'Otsu Area (ha)': f"{result['otsu_area']:.4f}",
            'Low (>0.05)': f"{result['threshold_areas'].get('low', 0):.4f}",
            'Moderate-Low (>0.075)': f"{result['threshold_areas'].get('moderate_low', 0):.4f}",
            'Moderate (>0.1)': f"{result['threshold_areas'].get('moderate', 0):.4f}",
            'High (>0.2)': f"{result['threshold_areas'].get('high', 0):.4f}",
            'Very High (>0.3)': f"{result['threshold_areas'].get('very_high', 0):.4f}",
            'Burned Area (ha)': f"{result['total_area']:.4f}",
            'Map File': result['map_file'].name,
            'Timestamp': timestamp
        }
        new_rows.append(row)
    
    all_rows = rows_to_keep + new_rows
    
    if all_rows:
        with open(summary_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'Analysis Name',
                'AOI Type',
                'Analysis Type',
                'Water Masked',
                'Resolution',
                'AOI Area (ha)',
                'Otsu Threshold',
                'Otsu Area (ha)',
                'Low (>0.05)',
                'Moderate-Low (>0.075)',
                'Moderate (>0.1)',
                'High (>0.2)',
                'Very High (>0.3)',
                'Burned Area (ha)',
                'Map File',
                'Timestamp'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            writer.writerows(all_rows)
    
    print(f"\n[CSV] 10m Analysis summary exported: {summary_file}")
    print(f"[CSV] Total 10m analyses in summary: {len(all_rows)}")
    
    return summary_file