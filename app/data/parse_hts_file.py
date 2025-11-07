import csv
import os
import re
import json
from typing import List
from datetime import date

# CONFIGURATION: Ensure this matches the file you downloaded
INPUT_FILE_NAME = 'htsdata.csv'
INPUT_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', INPUT_FILE_NAME)
OUTPUT_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'hs_codes.py')

def extract_hs_codes_from_csv(file_path: str) -> List[str]:
    """
    Reads the HTS CSV file, extracts the code from the first column, 
    and filters for the 6-digit Harmonized System codes.
    """
    print(f"Reading HTS data from: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"ERROR: Input CSV file not found at {file_path}. Please check your file name and path.")
        return []

    hs_codes = set()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Use csv.reader to handle standard CSV formatting
            reader = csv.reader(f)
            
            # Skip the header row (assuming the first row is headers)
            next(reader, None) 

            for row in reader:
                if not row:
                    continue
                
                # The HS/HTS code is always in the first column (index 0)
                raw_code = str(row[0]).strip()
                
                # Clean the code: remove all non-digit characters (like periods or dashes)
                clean_code = re.sub(r'\D', '', raw_code)

                # The international HS code is the first 6 digits
                if len(clean_code) >= 6:
                    hs_6_digit_code = clean_code[:6]
                    hs_codes.add(hs_6_digit_code)

    except Exception as e:
        print(f"An unexpected error occurred while reading or parsing the file: {e}")
        return []

    print(f"Found {len(hs_codes)} unique 6-digit HS codes.")
    return sorted(list(hs_codes))

def generate_hs_code_file(hs_codes: List[str]):
    """Writes the list of HS codes to a Python file."""
    
    os.makedirs(os.path.dirname(OUTPUT_FILE_PATH), exist_ok=True)
    codes_dump = json.dumps(hs_codes, indent=4)
    
    file_content = f"""
\"\"\"
Contains a comprehensive list of all HS 6-digit product codes derived from the U.S. HTS schedule.
Total Codes: {len(hs_codes)}
Last Generated: {date.today().isoformat()}
Source: U.S. Harmonized Tariff Schedule (HTS)
\"\"\"
from typing import List

ALL_HS_6_DIGIT_CODES: List[str] = {codes_dump}
"""
    with open(OUTPUT_FILE_PATH, 'w') as f:
        f.write(file_content.strip())
        
    print(f"Successfully generated {len(hs_codes)} HS 6-digit codes and saved to {OUTPUT_FILE_PATH}")


if __name__ == '__main__':
    all_codes = extract_hs_codes_from_csv(INPUT_FILE_PATH)
    if all_codes:
        generate_hs_code_file(all_codes)
    else:
        print("Process aborted because no HS codes were extracted.")
