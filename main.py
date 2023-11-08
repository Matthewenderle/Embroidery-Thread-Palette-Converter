import struct

threads = [["0345 - Moss", 110, 90, 33], ["0352 - Marsh",
                                          180, 171, 93], ["0442 - Tarnished Gold", 156, 132, 51]]

# threads = [["Kolor1", 0, 128, 200], ["Alpha", 112, 200, 0]]
# threads = [["Alphas2", 0, 128, 200]]

# Initialize variables
paletteName = 'Color Group 1'


# Specify the file path
file_path = 'your_file.bin'


def float_to_hex(f):
    return hex(struct.unpack('>I', struct.pack('>f', f))[0])


def RGB_to_HEX(value):
    percentage_value = value / 255.0
    ieee754_bytes = struct.pack('>f', percentage_value)
    return ieee754_bytes


def generate_hex():

    chunkCount = 2

    thread_output = b''

    for thread in range(len(threads)):
        name = threads[thread][0]
        r_byte = RGB_to_HEX(threads[thread][1])
        g_byte = RGB_to_HEX(threads[thread][2])
        b_byte = RGB_to_HEX(threads[thread][3])
        chunkCount = chunkCount + 1
        thread_name_byte = bytes.fromhex(
            name.encode('utf-16be').hex())

        thread_byte_length = struct.pack('>H', (len(name) * 2) + 22)

        thread_output += b'\x00\x01\x00\x00'  # add swatch start chunk

        print(struct.pack('>H', len(name)))

        thread_output += thread_byte_length  # add byte length (2+name+20)
        # add name byte length
        thread_output += struct.pack('>H', len(name) + 1)
        thread_output += thread_name_byte

        thread_output += b'\x00\x00'  # add spacer
        thread_output += b'\x52\x47\x42'  # add RGB
        thread_output += b'\x20'  # add spacer
        thread_output += r_byte
        thread_output += g_byte
        thread_output += b_byte
        thread_output += b'\x00\x02'  # add terminate swatch

        # print(f'thread_name_byte[{thread}]: {thread_name_byte}')

    ASEF_HEADER = b'\x41\x53\x45\x46'  # ASEF
    FILE_VERSION = b'\x00\x01\x00\x00'  # 1.0
    NUM_CHUNKS = struct.pack('>I', chunkCount)
    PALETTE_CHUNK_START = bytes.fromhex('C0010000001E')
    palette_name_byte_length = struct.pack('>H', len(paletteName) + 1)
    PALETTE_NAME = bytes.fromhex(
        paletteName.encode('utf-16be').hex()) + b'\x00\x00'

    PALETTE_CHUNK_END = b'\xC0\x02\x00\x00'
    EOF = b'\x00\x00'

    output = ASEF_HEADER + FILE_VERSION + NUM_CHUNKS + PALETTE_CHUNK_START
    output += palette_name_byte_length + PALETTE_NAME
    output += thread_output
    output += PALETTE_CHUNK_END + EOF

    return output


# Write the data to the binary file
with open(file_path, 'wb') as file:
    file.write(generate_hex())


print(f"Bytes written to '{file_path}' successfully.")


def dump_hexadecimal(buffer):
    hex_dump = ' '.join([f'{byte:02X}' for byte in buffer])
    return hex_dump


print(dump_hexadecimal(generate_hex()))
