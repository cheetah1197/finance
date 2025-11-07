import json
import os
from typing import List
from datetime import date

# CONFIGURATION: Update this if you downloaded a different file name
INPUT_FILE_NAME = 'htsdata.json'
INPUT_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', INPUT_FILE_NAME)
OUTPUT_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'hs_codes.py')

def extract_hs_codes_from_json(file_path: str) -> List[str]:
    """
    Reads the HTS JSON file, extracts the 6-digit Harmonized System codes,
    and returns a sorted, unique list.
    """
    print(f"Reading HTS data from: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"ERROR: Input file not found at {file_path}. Please check your file name and path.")
        return []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print("ERROR: Failed to parse JSON. Is the file valid JSON?")
        return []
    except Exception as e:
        print(f"An unexpected error occurred while reading the file: {e}")
        return []

    hs_codes = set()
    
    # The USITC JSON structure typically contains a list of tariff items.
    for item in data:
        # The HTS number is the key field we are interested in.
        hts_number = str(item.get('htsNumber', '')).replace('.', '').strip()
        
        # We need the first 6 digits of the HTS code.
        # HTS codes can be 10 digits (e.g., '0101210000').
        if len(hts_number) >= 6 and hts_number.isdigit():
            # Extract the 6-digit HS code (the international standard)
            hs_6_digit_code = hts_number[:6]
            hs_codes.add(hs_6_digit_code)

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
    all_codes = extract_hs_codes_from_json(INPUT_FILE_PATH)
    if all_codes:
        generate_hs_code_file(all_codes)
    else:
        print("Process aborted because no HS codes were extracted.")
