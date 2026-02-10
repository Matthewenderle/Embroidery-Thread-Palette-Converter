import struct
import configparser
import psycopg2
import re
import os
from pathlib import Path

config = configparser.ConfigParser()
config.read('config.ini')

class CustomError(Exception):
    pass

def dump_hexadecimal(buffer):
    return ' '.join([f'{byte:02X}' for byte in buffer])

def float_to_hex(f):
    return hex(struct.unpack('>I', struct.pack('>f', f))[0])

def RGB_to_HEX(value):
    percentage_value = value / 255.0
    ieee754_bytes = struct.pack('>f', percentage_value)
    return ieee754_bytes

def create_thread_chunk(thread):
    try:
        code = thread[0] if len(thread) > 0 else "Unknown"
        name = thread[1] if len(thread) > 1 and thread[1] is not None else ""
        red = thread[2] if len(thread) > 2 and thread[2] is not None else 0
        green = thread[3] if len(thread) > 3 and thread[3] is not None else 0
        blue = thread[4] if len(thread) > 4 and thread[4] is not None else 0
        
        full_name = f"{code} - {name}" if name else code
        
        r_byte = RGB_to_HEX(red)
        g_byte = RGB_to_HEX(green)
        b_byte = RGB_to_HEX(blue)
        thread_name_byte = bytes.fromhex(full_name.encode('utf-16be').hex())
        thread_byte_length = struct.pack('>H', (len(full_name) * 2) + 22)

        chunk = (
            b'\x00\x01\x00\x00' +  # swatch start chunk
            thread_byte_length +
            struct.pack('>H', len(full_name) + 1) +
            thread_name_byte +
            b'\x00\x00' +  # spacer
            b'\x52\x47\x42' +  # RGB
            b'\x20' +  # spacer
            r_byte +
            g_byte +
            b_byte +
            b'\x00\x02'  # terminate swatch
        )

        return chunk
    except Exception as e:
        raise CustomError(f"Failed to save data to file. Error: {e} on {thread}")

def generate_hex(threads, palette_name):
    chunk_count = 2
    thread_output = b''
    
    for thread in threads:
        thread_output += create_thread_chunk(thread)
        chunk_count += 1
    
    ASEF_HEADER = b'\x41\x53\x45\x46'  # ASEF
    FILE_VERSION = b'\x00\x01\x00\x00'  # 1.0
    NUM_CHUNKS = struct.pack('>I', chunk_count)
    PALETTE_CHUNK_START = bytes.fromhex('C0010000')
    palette_byte_length = struct.pack('>H', 4 + len(palette_name)*2)
    palette_name_byte_length = struct.pack('>H', len(palette_name))
    PALETTE_NAME = bytes.fromhex(palette_name.encode('utf-16be').hex()) + b'\x00\x00'
    PALETTE_CHUNK_END = b'\xC0\x02\x00\x00'
    EOF = b'\x00\x00'
    
    output = (
        ASEF_HEADER +
        FILE_VERSION +
        NUM_CHUNKS +
        PALETTE_CHUNK_START +
        palette_byte_length +
        palette_name_byte_length +
        PALETTE_NAME +
        thread_output +
        PALETTE_CHUNK_END +
        EOF
    )
    
    return output

def sanitize_file_name(file_name):
    sanitized_name = file_name.replace(' ', '_')
    sanitized_name = re.sub(r'[^\w\s.-]', '', sanitized_name)
    return sanitized_name

def parse_existing_ase_file(file_path):
    """Parse existing ASE file to extract thread information and preserve structure"""
    if not os.path.exists(file_path):
        return None, {}
    
    try:
        with open(file_path, 'rb') as file:
            content = file.read()
            
        # Skip header and get to the thread data
        # ASEF header (4) + version (4) + chunk count (4) + palette start chunk (4 + variable length)
        if content[:4] != b'ASEF':
            return None, {}
        
        threads_data = {}
        palette_name = ""
        
        # Find palette name
        palette_start_pos = content.find(b'\xC0\x01\x00\x00')
        if palette_start_pos != -1:
            palette_length_pos = palette_start_pos + 4
            palette_length = struct.unpack('>H', content[palette_length_pos:palette_length_pos + 2])[0]
            name_length_pos = palette_length_pos + 2
            name_length = struct.unpack('>H', content[name_length_pos:name_length_pos + 2])[0]
            name_start = name_length_pos + 2
            name_end = name_start + (name_length - 1) * 2  # UTF-16BE
            
            try:
                palette_name = content[name_start:name_end].decode('utf-16be')
            except:
                palette_name = ""
        
        # Parse thread swatches
        pos = 12  # Start after ASEF header
        while pos < len(content):
            if pos + 4 > len(content):
                break
                
            chunk_type = content[pos:pos + 4]
            
            if chunk_type == b'\x00\x01\x00\x00':  # Thread swatch
                if pos + 6 > len(content):
                    break
                    
                chunk_length = struct.unpack('>H', content[pos + 4:pos + 6])[0]
                name_length = struct.unpack('>H', content[pos + 6:pos + 8])[0]
                
                if pos + 8 + (name_length - 1) * 2 > len(content):
                    break
                
                name_bytes = content[pos + 8:pos + 8 + (name_length - 1) * 2]
                try:
                    thread_name = name_bytes.decode('utf-16be')
                except:
                    thread_name = "Unknown"
                
                # Extract RGB values (they're after the name + some padding)
                rgb_start = pos + 8 + (name_length - 1) * 2 + 2 + 4  # name + padding + "RGB "
                if rgb_start + 12 <= len(content):
                    r_bytes = content[rgb_start:rgb_start + 4]
                    g_bytes = content[rgb_start + 4:rgb_start + 8]
                    b_bytes = content[rgb_start + 8:rgb_start + 12]
                    
                    # Convert from IEEE 754 float back to RGB values
                    r_float = struct.unpack('>f', r_bytes)[0]
                    g_float = struct.unpack('>f', g_bytes)[0]
                    b_float = struct.unpack('>f', b_bytes)[0]
                    
                    r = int(r_float * 255)
                    g = int(g_float * 255)
                    b = int(b_float * 255)
                    
                    threads_data[thread_name] = {'red': r, 'green': g, 'blue': b}
                
                pos += chunk_length + 6
            else:
                # Skip non-thread chunks
                if pos + 6 > len(content):
                    break
                chunk_length = struct.unpack('>H', content[pos + 4:pos + 6])[0]
                pos += chunk_length + 6
        
        return palette_name, threads_data
    except Exception as e:
        print(f"Warning: Could not parse existing file {file_path}: {e}")
        return None, {}

def threads_are_different(db_threads, file_threads, palette_name_db, palette_name_file):
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
    file_path = './adobe-swatches/'
    file_path += sanitize_file_name(f'{chart[3]}.ase' if chart[1] == chart[3] else f'{chart[3]}_{chart[1]}.ase')
    
    # Get threads
    cursor.execute(f'''SELECT thread_cones.code, thread_cones.name, thread_cones.red, thread_cones.green, 
                              thread_cones.blue, thread_cones.threadChartId, thread_cones.id
                      FROM thread_cones
                      WHERE thread_cones.disabled = 0 AND thread_cones.threadChartId = {chart[0]}''')
    threads = cursor.fetchall()
    
    parsed_threads = [[row[i] if i < len(row) else None for i in range(5)] for row in threads]
    
    # Parse existing file to check for changes
    palette_name = chart[1] if chart[1] == chart[3] else f'{chart[3]} - {chart[1]}'
    existing_palette_name, existing_threads = parse_existing_ase_file(file_path)
    
    # Only write file if there are changes
    if threads_are_different(parsed_threads, existing_threads, palette_name, existing_palette_name):
        # Ensure directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w+b') as file:
            file.write(generate_hex(parsed_threads, palette_name))
        
        print(f"Updated '{file_path}' - changes detected.")
    else:
        print(f"Skipped '{file_path}' - no changes detected.")

cursor.close()
conn.close()