import os
import csv
import json
from .constants import CSV_FILENAME

def init_csv():
    """Init the CSV with detailed columns."""
    os.makedirs(os.path.dirname(CSV_FILENAME), exist_ok=True)
    if not os.path.isfile(CSV_FILENAME):
        with open(CSV_FILENAME, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                "Timestamp", 
                "Scenario", 
                "Batch", 
                "BatchID", 
                "Time(s)", 
                "200 (OK)", 
                "400 (Bad Req)", 
                "401/403 (Auth/Block)", 
                "429 (Rate Limit)", 
                "500+ (Errors)", 
                "TotalReqs"
            ])

def load_csv_data(filename_key):
    """Loads dynamic data (shop_ids, tokens) from a CSV file."""
    if not filename_key: return []
    if not filename_key.endswith('.csv'): filename_key += '.csv'
    
    # Check existence
    if not os.path.isfile(filename_key):
        print(f"⚠️ [WARN] CSV {filename_key} not found.")
        return []
    
    data = []
    try:
        with open(filename_key, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Clean whitespace keys/values
                data.append({k.strip(): v.strip() for k, v in row.items() if k})
    except Exception as e:
        print(f"❌ [ERROR] Could not read CSV: {e}")
        
    return data

def append_result_to_csv(timestamp, scenario, batch_num, batch_id, duration, stats, total):
    """Writes a single result row to the report CSV."""
    try:
        with open(CSV_FILENAME, mode='a', newline='') as f:
            csv.writer(f).writerow([
                timestamp,
                scenario, 
                batch_num, 
                batch_id, 
                f"{duration:.2f}",
                stats["200"],
                stats["400"],
                stats["401_403"],
                stats["429"],
                stats["500_other"],
                total
            ])
    except Exception as e:
        print(f"❌ Error writing CSV: {e}")

def load_endpoint_config(endpoint_name, base_dir):
    """Loads the JSON config for a specific endpoint."""
    if not endpoint_name.endswith('.json'):
        endpoint_name += '.json'
    
    config_path = os.path.join(base_dir, endpoint_name)
    
    if not os.path.exists(config_path):
        return None, f"Configuration file not found at: {config_path}"

    print(f"📂 Loading configuration from: {config_path}")
    try:
        with open(config_path, 'r') as f:
            data = json.load(f)
        # Normalize to list
        scenarios = [data] if isinstance(data, dict) else data
        return scenarios, None
    except json.JSONDecodeError:
        return None, f"Invalid JSON format in {config_path}"