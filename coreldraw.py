import uuid
import configparser
import psycopg2
import re

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
    
    with open(file_path, 'w', encoding='utf-8-sig') as file:
        palette_name = chart[1] if chart[1] == chart[3] else f'{chart[3]} - {chart[1]}'
        file.write(generate_cdr(parsed_threads, palette_name))
    
    print(f"Bytes written to '{file_path}' successfully.")

cursor.close()
conn.close()
