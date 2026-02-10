import uuid
import configparser
import psycopg2
import re
import os
from pathlib import Path
import xml.etree.ElementTree as ET

config = configparser.ConfigParser()
config.read('config.ini')

class CustomError(Exception):
    pass

def rgb_to_corel_tints(red, green, blue):
    corel_red = red / 255
    corel_green = green / 255
    corel_blue = blue / 255
    return f'{corel_red},{corel_green},{corel_blue}'

def create_thread_chunk(thread, id):
    try:
        code = thread[0] if len(thread) > 0 else "Unknown"
        name = thread[1] if len(thread) > 1 and thread[1] is not None else ""
        red = thread[2] if len(thread) > 2 and thread[2] is not None else 0
        green = thread[3] if len(thread) > 3 and thread[3] is not None else 0
        blue = thread[4] if len(thread) > 4 and thread[4] is not None else 0
        
        full_name = f"{code} - {name}" if name else code
        
        tints = rgb_to_corel_tints(red, green, blue)
        chunk = f'<color name="{full_name}" cs="RGB" tints="{tints}" fixedID="{id}"/>'
        return chunk
    except Exception as e:
        raise CustomError(f"Failed to save data to file. Error: {e} on {thread}")

def parse_existing_xml_file(file_path):
    """Parse existing XML file to extract thread information and preserve IDs"""
    if not os.path.exists(file_path):
        return None, {}, {}
    
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        palette_name = root.get('name', '')
        threads_data = {}
        thread_ids = {}  # Map from thread name to existing ID
        
        colors = root.find('.//colors/page')
        if colors is not None:
            for color in colors.findall('color'):
                name = color.get('name', '')
                tints = color.get('tints', '')
                fixed_id = color.get('fixedID', '')
                
                if tints and name:
                    try:
                        # Parse RGB tints (comma-separated values between 0 and 1)
                        r, g, b = map(float, tints.split(','))
                        red = int(r * 255)
                        green = int(g * 255)
                        blue = int(b * 255)
                        
                        threads_data[name] = {'red': red, 'green': green, 'blue': blue}
                        if fixed_id:
                            thread_ids[name] = fixed_id
                    except ValueError:
                        continue
        
        return palette_name, threads_data, thread_ids
    except Exception as e:
        print(f"Warning: Could not parse existing file {file_path}: {e}")
        return None, {}, {}

def threads_are_different_xml(db_threads, file_threads, palette_name_db, palette_name_file):
    """Compare database threads with file threads to detect changes"""
    if palette_name_db != palette_name_file:
        return True
    
    # Create a set of thread names from database
    db_thread_names = set()
    db_thread_data = {}
    
    for thread in db_threads:
        code = thread[0] if len(thread) > 0 else "Unknown"
        name = thread[1] if len(thread) > 1 and thread[1] is not None else ""
        red = thread[2] if len(thread) > 2 and thread[2] is not None else 0
        green = thread[3] if len(thread) > 3 and thread[3] is not None else 0
        blue = thread[4] if len(thread) > 4 and thread[4] is not None else 0
        
        full_name = f"{code} - {name}" if name else code
        db_thread_names.add(full_name)
        db_thread_data[full_name] = {'red': red, 'green': green, 'blue': blue}
    
    file_thread_names = set(file_threads.keys())
    
    # Check if thread sets are different
    if db_thread_names != file_thread_names:
        return True
    
    # Check if any thread colors are different
    for name in db_thread_names:
        if name in file_threads:
            db_color = db_thread_data[name]
            file_color = file_threads[name]
            if (db_color['red'] != file_color['red'] or 
                db_color['green'] != file_color['green'] or 
                db_color['blue'] != file_color['blue']):
                return True
    
    return False

def generate_cdr_with_preserved_ids(threads, palette_name, existing_thread_ids):
    """Generate CDR content while preserving existing thread IDs"""
    thread_chunks = []
    used_ids = set(existing_thread_ids.values())
    next_id = 1
    
    for thread in threads:
        code = thread[0] if len(thread) > 0 else "Unknown"
        name = thread[1] if len(thread) > 1 and thread[1] is not None else ""
        full_name = f"{code} - {name}" if name else code
        
        # Use existing ID if available, otherwise assign new one
        if full_name in existing_thread_ids:
            thread_id = existing_thread_ids[full_name]
        else:
            # Find next available ID
            while str(next_id) in used_ids:
                next_id += 1
            thread_id = str(next_id)
            used_ids.add(thread_id)
            next_id += 1
        
        thread_chunks.append(create_thread_chunk(thread, thread_id))
    
    thread_output = '\n'.join(thread_chunks)
    
    XML_HEADER = '<?xml version="1.0" encoding="UTF-8"?>\n'
    AUTHOR_BLOCK = '<!-- Created by Matthew Enderle using https://github.com/Matthewenderle/ThreadChart-to-Adobe-Swatch -->\n'
    CREDIT_BLOCK = '<!-- Provided for free by The Embroidery Nerds, LLC. -->\n'
    DISCLAIMER_BLOCK = (
        '<!-- Disclaimer: The following XML file may contain names that are registered trademarks or copyrighted material owned by their respective owners. -->\n'
        '<!-- The use of such names is for descriptive purposes only. All rights to these names are owned by their respective owners. -->\n'
    )
    PALETTE_HEADER = f'<palette guid="{uuid.uuid4()}" name="{palette_name}" locked="true">\n'
    PALETTE_FOOTER = '</palette>'
    
    output = (
        XML_HEADER + AUTHOR_BLOCK + CREDIT_BLOCK + DISCLAIMER_BLOCK + PALETTE_HEADER + '<colors>\n<page>\n' +
        thread_output + '\n</page>\n</colors>\n' + PALETTE_FOOTER
    )
    return output

def generate_cdr(threads, palette_name):
    thread_output = '\n'.join(create_thread_chunk(thread, i + 1) for i, thread in enumerate(threads))
    
    XML_HEADER = '<?xml version="1.0" encoding="UTF-8"?>\n'
    AUTHOR_BLOCK = '<!-- Created by Matthew Enderle using https://github.com/Matthewenderle/ThreadChart-to-Adobe-Swatch -->\n'
    CREDIT_BLOCK = '<!-- Provided for free by The Embroidery Nerds, LLC. -->\n'
    DISCLAIMER_BLOCK = (
        '<!-- Disclaimer: The following XML file may contain names that are registered trademarks or copyrighted material owned by their respective owners. -->\n'
        '<!-- The use of such names is for descriptive purposes only. All rights to these names are owned by their respective owners. -->\n'
    )
    PALETTE_HEADER = f'<palette guid="{uuid.uuid4()}" name="{palette_name}" locked="true">\n'
    PALETTE_FOOTER = '</palette>'
    
    output = (
        XML_HEADER + AUTHOR_BLOCK + CREDIT_BLOCK + DISCLAIMER_BLOCK + PALETTE_HEADER + '<colors>\n<page>\n' +
        thread_output + '\n</page>\n</colors>\n' + PALETTE_FOOTER
    )
    return output

def sanitize_file_name(file_name):
    sanitized_name = file_name.replace(' ', '_')
    sanitized_name = re.sub(r'[^\w\s.-]', '', sanitized_name)
    return sanitized_name

db_params = {
    'host': config.get('Database', 'host'),
    'dbname': config.get('Database', 'database'),
    'user': config.get('Database', 'user'),
    'password': config.get('Database', 'pass'),
}

conn = psycopg2.connect(**db_params)
cursor = conn.cursor()

# Get Charts
cursor.execute('''SELECT thread_charts.id, thread_charts.chart, thread_charts.chartbrandid, thread_brands.brand
                  FROM thread_charts
                  INNER JOIN thread_brands ON thread_charts.chartbrandid = thread_brands.id
                  WHERE thread_charts.disabled = 0''')
charts = cursor.fetchall()

for chart in charts:
    file_path = './corel-swatches/'
    file_path += sanitize_file_name(f'{chart[3]}.xml' if chart[1] == chart[3] else f'{chart[3]}_{chart[1]}.xml')
    
    # Get threads
    cursor.execute(f'''SELECT thread_cones.code, thread_cones.name, thread_cones.red, thread_cones.green, 
                              thread_cones.blue, thread_cones.threadChartId, thread_cones.id
                      FROM thread_cones
                      WHERE thread_cones.disabled = 0 AND thread_cones.threadChartId = {chart[0]}''')
    threads = cursor.fetchall()
    
    parsed_threads = [[row[i] if i < len(row) else None for i in range(5)] for row in threads]
    
    # Parse existing file to check for changes and preserve IDs
    palette_name = chart[1] if chart[1] == chart[3] else f'{chart[3]} - {chart[1]}'
    existing_palette_name, existing_threads, existing_thread_ids = parse_existing_xml_file(file_path)
    
    # Only write file if there are changes
    if threads_are_different_xml(parsed_threads, existing_threads, palette_name, existing_palette_name):
        # Ensure directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8-sig') as file:
            file.write(generate_cdr_with_preserved_ids(parsed_threads, palette_name, existing_thread_ids))
        
        print(f"Updated '{file_path}' - changes detected.")
    else:
        print(f"Skipped '{file_path}' - no changes detected.")

cursor.close()
conn.close()
