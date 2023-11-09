import uuid
import configparser
import mysql.connector
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
        name = thread[0]
        red = thread[1]
        green = thread[2]
        blue = thread[3]

        tints = rgb_to_corel_tints(red, green, blue)

        chunk = (
            f'<color name="{name}" cs="RGB" tints="{tints}" fixedID="{id}"/>\n'
        )

        return chunk
    except Exception as e:
        raise CustomError(
            f"Failed to save data to file. Error: {e} on {thread}")


def generate_cdr(threads, palette_name):
    thread_output = ''
    i = 1

    for thread in threads:
        thread_output += create_thread_chunk(thread, i)
        i = i + 1

    XML_HEADER = '<?xml version="1.0" encoding="UTF-8"?>\n'
    AUTHOR_BLOCK = '<!-- Created by Matthew Enderle using https://github.com/Matthewenderle/ThreadChart-to-Adobe-Swatch -->\n'
    CREDIT_BLOCK = '<!-- Provided for free by The Embroidery Nerds, LLC. -->\n'
    DISCLAIMER_BLOCK = '<!-- Disclaimer: The following XML file may contain names that are registered trademarks or copyrighted material owned by their respective owners.-->\n'
    DISCLAIMER_BLOCK += '<!--             The use of such names is for descriptive purposes only. All rights to these names are owned by their respective owners. -->\n'
    PALETTE_HEADER = f'<palette guid="{uuid.uuid4()}" name="{palette_name}" locked="true">\n'
    PALETTE_FOOTER = '</palette>\n'

    output = (
        XML_HEADER +
        AUTHOR_BLOCK +
        CREDIT_BLOCK +
        DISCLAIMER_BLOCK +
        PALETTE_HEADER +
        '<colors>\n' +
        '<page>\n' +
        thread_output +
        '</page>\n' +
        '</colors>\n' +
        PALETTE_FOOTER
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
    charts.append(row)


for chart in charts:
    file_path = './corel-swatches/'
    if chart[1] == chart[3]:
        file_path += sanitize_file_name(f'{chart[3]}.xml')
    else:
        file_path += sanitize_file_name(f'{chart[3]}_{chart[1]}.xml')

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

    with open(file_path, 'w', encoding='utf-8-sig') as file:
        if chart[1] == chart[3]:
            palette_name = chart[1]
        else:
            palette_name = f'{chart[3]} - {chart[1]}'

        file.write(generate_cdr(parsed_threads, palette_name))

    print(f"Bytes written to '{file_path}' successfully.")

cursor.close()
conn.close()
