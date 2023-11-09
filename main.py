import struct


def float_to_hex(f):
    return hex(struct.unpack('>I', struct.pack('>f', f))[0])


def RGB_to_HEX(value):
    percentage_value = value / 255.0
    ieee754_bytes = struct.pack('>f', percentage_value)
    return ieee754_bytes


def create_thread_chunk(thread):
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


def generate_hex(threads):
    chunk_count = 2
    thread_output = b''

    for thread in threads:
        thread_output += create_thread_chunk(thread)
        chunk_count += 1

    ASEF_HEADER = b'\x41\x53\x45\x46'  # ASEF
    FILE_VERSION = b'\x00\x01\x00\x00'  # 1.0
    NUM_CHUNKS = struct.pack('>I', chunk_count)
    PALETTE_CHUNK_START = bytes.fromhex('C0010000001E')
    palette_name_byte_length = struct.pack('>H', len(paletteName) + 1)
    PALETTE_NAME = bytes.fromhex(
        paletteName.encode('utf-16be').hex()) + b'\x00\x00'
    PALETTE_CHUNK_END = b'\xC0\x02\x00\x00'
    EOF = b'\x00\x00'

    output = (
        ASEF_HEADER +
        FILE_VERSION +
        NUM_CHUNKS +
        PALETTE_CHUNK_START +
        palette_name_byte_length +
        PALETTE_NAME +
        thread_output +
        PALETTE_CHUNK_END +
        EOF
    )

    return output


# Initialize variables
paletteName = 'Color Group 1'
threads = [
    ["0345 - Moss", 110, 90, 33],
    ["0352 - Marsh", 180, 171, 93],
    ["0442 - Tarnished Gold", 156, 132, 51]
]

# TODO Specify the file path via arguments
file_path = 'your_file.bin'

with open(file_path, 'wb') as file:
    file.write(generate_hex(threads))

print(f"Bytes written to '{file_path}' successfully.")


# def dump_hexadecimal(buffer):
#     hex_dump = ' '.join([f'{byte:02X}' for byte in buffer])
#     return hex_dump


# print(dump_hexadecimal(generate_hex()))
