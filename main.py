import struct
import configparser
import mysql.connector
import re


config = configparser.ConfigParser()
config.read('config.ini')


class CustomError(Exception):
    pass


def dump_hexadecimal(buffer):
    hex_dump = ' '.join([f'{byte:02X}' for byte in buffer])
    return hex_dump


def float_to_hex(f):
    return hex(struct.unpack('>I', struct.pack('>f', f))[0])


def RGB_to_HEX(value):
    percentage_value = value / 255.0
    ieee754_bytes = struct.pack('>f', percentage_value)
    return ieee754_bytes


def create_thread_chunk(thread):
    try:
        name = thread[0]
        r_byte = RGB_to_HEX(thread[1])
        g_byte = RGB_to_HEX(thread[2])
        b_byte = RGB_to_HEX(thread[3])
        thread_name_byte = bytes.fromhex(name.encode('utf-16be').hex())
        thread_byte_length = struct.pack('>H', (len(name) * 2) + 22)

        chunk = (
            b'\x00\x01\x00\x00' +  # swatch start chunk
            thread_byte_length +
            struct.pack('>H', len(name) + 1) +
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
        raise CustomError(
            f"Failed to save data to file. Error: {e} on {thread}")


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
    PALETTE_NAME = bytes.fromhex(
        palette_name.encode('utf-16be').hex()) + b'\x00\x00'
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

    # print(dump_hexadecimal(output))

    return output


def sanitize_file_name(file_name):
    sanitized_name = file_name.replace(' ', '_')
    sanitized_name = re.sub(r'[^\w\s.-]', '', sanitized_name)

    return sanitized_name


db_params = {
    'host': config.get('Database', 'host'),
    'database': config.get('Database', 'database'),
    'user': config.get('Database', 'user'),
    'password': config.get('Database', 'pass'),
}

conn = mysql.connector.connect(**db_params)
cursor = conn.cursor()

# Get Charts
charts = []
cursor.execute('''SELECT
	thread_charts.id, 
	thread_charts.chart, 
	thread_charts.threadBrandId, 
	thread_brands.brand
FROM
	thread_charts
	INNER JOIN
	thread_brands
	ON 
		thread_charts.threadBrandId = thread_brands.id
WHERE
	thread_charts.disabled = 0 ''')  # AND thread_charts.id = 47
rows = cursor.fetchall()
for row in rows:
    # print(row)
    charts.append(row)


for chart in charts:
    file_path = './swatches/'
    if chart[1] == chart[3]:
        file_path += sanitize_file_name(f'{chart[3]}.ase')
    else:
        file_path += sanitize_file_name(f'{chart[3]}_{chart[1]}.ase')

    # Get threads
    threads = []
    cursor.execute(f'''SELECT
	thread_cones.`code`, 
	thread_cones.`name`, 
	thread_cones.red, 
	thread_cones.green, 
	thread_cones.blue, 
	thread_cones.threadChartId AS chartId,
    thread_cones.id
FROM
	thread_cones
WHERE
	thread_cones.disabled = 0 AND
	thread_cones.threadChartId = {chart[0]};''')
    rows = cursor.fetchall()

    parsed_threads = []

    for row in rows:
        if row[0] == '':
            name = row[1]
        elif row[1] == '':
            name = row[0]
        else:
            name = f'{row[0]} - {row[1]}'

        parsed_threads.append([name, row[2], row[3], row[4], row[5], row[6]])

    with open(file_path, 'w+b') as file:
        file.write(generate_hex(parsed_threads, chart[1]))

    print(f"Bytes written to '{file_path}' successfully.")

cursor.close()
conn.close()
