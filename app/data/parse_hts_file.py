import csv
import os
import re
import json
from typing import List, Dict, Any
from datetime import date

# CONFIGURATION
INPUT_FILE_NAME = 'htsdata.csv'
INPUT_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', INPUT_FILE_NAME)
OUTPUT_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'product_list.py')

# *** ADJUST THIS VALUE ***
# Try 2 first, then 3, then 4 until you see actual descriptions in the output file.
COLUMN_INDEX_DESCRIPTION = 2 


def extract_product_data_from_csv(file_path: str) -> List[Dict[str, str]]:
    """
    Reads the HTS CSV file, extracts the 6-digit HS code and its description.
    """
    print(f"Reading HTS data from: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"ERROR: Input CSV file not found at {file_path}. Please ensure it is named '{INPUT_FILE_NAME}'.")
        return []

    products = {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None) # Skip the header row 

            for row in reader:
                if len(row) < (COLUMN_INDEX_DESCRIPTION + 1): continue
                
                # Column 0 is the full HTS code (e.g., '0101.21.0000')
                raw_code = str(row[0]).strip()
                
                # *** UPDATED: Using the configurable index for description ***
                description = str(row[COLUMN_INDEX_DESCRIPTION]).strip() 
                
                clean_code = re.sub(r'\D', '', raw_code)

                # We only care about unique 6-digit codes
                if len(clean_code) >= 6:
                    hs_6_digit_code = clean_code[:6]
                    
                    # Store only if we haven't seen this 6-digit code or if the description is better
                    if hs_6_digit_code not in products or len(description) > len(products[hs_6_digit_code]['description']):
                        products[hs_6_digit_code] = {
                            'code': hs_6_digit_code,
                            'description': description
                        }

    except Exception as e:
        print(f"An unexpected error occurred while reading or parsing the file: {e}")
        return []

    print(f"Found {len(products)} unique 6-digit HS codes with descriptions.")
    return list(products.values())

def generate_product_list_file(products: List[Dict[str, str]]):
    """Writes the list of products to a Python file."""
    
    os.makedirs(os.path.dirname(OUTPUT_FILE_PATH), exist_ok=True)
    products_dump = json.dumps(products, indent=4)
    
    file_content = f"""
\"\"\"
Contains a structured list of all 6-digit HS product codes and descriptions.
Total Codes: {len(products)}
Last Generated: {date.today().isoformat()}
Source: U.S. Harmonized Tariff Schedule (HTS)
\"\"\"
from typing import List, Dict, Any

ALL_HS_PRODUCTS: List[Dict[str, str]] = {products_dump}
"""
    with open(OUTPUT_FILE_PATH, 'w') as f:
        f.write(file_content.strip())
        
    print(f"Successfully generated {len(products)} product records and saved to {OUTPUT_FILE_PATH}")


if __name__ == '__main__':
    all_products = extract_product_data_from_csv(INPUT_FILE_PATH)
    if all_products:
        generate_product_list_file(all_products)
    else:
        print("Process aborted because no products were extracted.")
