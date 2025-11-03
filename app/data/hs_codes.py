import httpx
import xml.etree.ElementTree as ET
import json
import os
import asyncio
from typing import List
from datetime import date

# The WITS SDMX Codelist API endpoint for products
WITS_CODELIST_URL = "https://wits.worldbank.org/API/V1/SDMX/Codelist/WBG_WITS/CL_TS_PRODUCTCODE_WITS"
# Define the output path relative to the script's location
OUTPUT_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'hs_codes.py')

# Define a dictionary containing the headers you want to send.
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


def parse_wits_product_codelist(xml_data: str) -> List[str]:
    """
    Parses the WITS SDMX XML data using standard ElementTree to extract 6-digit HS codes.
    The SDMX XML format is complex and uses namespaces, which ElementTree handles via the findall method.
    """
    # 1. Define the necessary namespaces for SDMX structure
    namespaces = {
        's': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure',
        'c': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common'
    }
    
    try:
        root = ET.fromstring(xml_data)
        hs_codes = []
        
        # 2. Find all <Code> elements within the XML structure.
        # The correct XPath expression finds all 'Code' tags under the 'Codelist' element.
        # We need to use the full namespace in the tag name for accurate matching.
        
        # Look for the Codelist element
        codelist_element = root.find('.//s:Codelist', namespaces)
        
        if codelist_element is not None:
            # Find all Code elements within the Codelist
            for item in codelist_element.findall('s:Code', namespaces):
                # The actual code value is stored in the 'value' attribute
                code = item.get('value')
                
                # 3. Crucial manipulation: filter down to only strict 6-digit numeric codes.
                if code and len(code) == 6 and code.isdigit():
                    hs_codes.append(code)
        
        # Remove duplicates and sort the final list
        return sorted(list(set(hs_codes)))
        
    except ET.ParseError as e:
        print(f"Error parsing XML data: {e}")
        return []
    except Exception as e:
        print(f"Error processing WITS product codelist: {e}")
        return []

def generate_hs_code_file(hs_codes: List[str]):
    """
    Writes the list of HS codes to a Python file (`app/data/hs_codes.py`).
    It uses JSON dump with indent=4 for clean, multi-line list formatting.
    """
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(OUTPUT_FILE_PATH), exist_ok=True)
    
    # Use json.dumps to format the Python list nicely inside the string
    codes_dump = json.dumps(hs_codes, indent=4)
    
    file_content = f"""
\"\"\"
Contains a comprehensive, programmatically-fetched list of all WITS-supported HS 6-digit product codes.
Total Codes: {len(hs_codes)}
Last Generated: {date.today().isoformat()}
\"\"\"
from typing import List

ALL_HS_6_DIGIT_CODES: List[str] = {codes_dump}
"""
    with open(OUTPUT_FILE_PATH, 'w') as f:
        f.write(file_content.strip())
        
    print(f"Successfully generated {len(hs_codes)} HS 6-digit codes and saved to {OUTPUT_FILE_PATH}")


async def fetch_and_write_hs_codes():
    # 1. The headers dictionary is defined here
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # 2. We create an asynchronous client object
        async with httpx.AsyncClient(timeout=60.0) as client:
            # 3. The request is made using client.get(), and the headers are passed in!
            response = await client.get(WITS_CODELIST_URL, headers=headers) # <-- THIS IS THE LINE!
            response.raise_for_status()
            
            # The WITS metadata API returns XML by default
            hs_codes = parse_wits_product_codelist(response.text)
            
            if hs_codes:
                generate_hs_code_file(hs_codes)
            else:
                print("ERROR: Failed to retrieve or parse HS codes. The generated list is empty.")
                
    except httpx.HTTPStatusError as e:
        print(f"ERROR: HTTP error {e.response.status_code} fetching HS codes. Details: {e}")
    except Exception as e:
        print(f"ERROR: An unexpected error occurred during fetching: {e}")

if __name__ == '__main__':
    # Execute the asynchronous main function
    asyncio.run(fetch_and_write_hs_codes())
