import serial
import struct
import threading
import time
import zlib

SERIAL_PORT = '/dev/ttyACM0'
BAUDRATE = 115200

SOF  = 0xAA
EOF  = 0xBB

PACKET_CMD    = 0x01
PACKET_HEADER = 0x02
PACKET_DATA   = 0x03
PACKET_RESP   = 0x04

CMD_START = 0xA0
CMD_END   = 0xA1

CHUNK_SIZE = 128

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

ser_lock = threading.Lock()

def crc32(data):
    return 0
#    return zlib.crc32(data) & 0xFFFFFFFF

def build_frame(packet_type, payload: bytes) -> bytes:
    frame = bytearray()
    frame.append(SOF)
    frame.append(packet_type)
    frame += struct.pack('<H', len(payload))
    frame += payload
    frame += struct.pack('<I', crc32(payload))
    frame.append(EOF)
    return frame

def wait_for_ack(ser, timeout=2.0) -> bool:
    start = time.time()
    buffer = bytearray()

    while time.time() - start < timeout:
        with ser_lock:
            byte = ser.read()
        if byte:
            print(f"Received byte: 0x{byte[0]:02X}")  # Debug print
            buffer.append(byte[0])

            if len(buffer) >= 10 and buffer[0] == SOF and buffer[1] == PACKET_RESP:
                status = buffer[4]
                print(f"Full frame received, status: 0x{status:02X}")
                return status == RESP_ACK

    print("Timeout: No valid ACK received")
    return False



def send_cmd(ser, cmd_id):
    payload = bytes([cmd_id])
    frame = build_frame(PACKET_CMD, payload)
    ser.write(frame)

def send_header(ser, fw_size, fw_crc, version=0):
    header = struct.pack('<III', fw_size, fw_crc, version) + b'\x00' * 4
    frame = build_frame(PACKET_HEADER, header)
    ser.write(frame)

def send_data_chunks(ser, fw_data):
    for i in range(0, len(fw_data), CHUNK_SIZE):
        chunk = fw_data[i:i+CHUNK_SIZE]
        frame = build_frame(PACKET_DATA, chunk)
        ser.write(frame)

        if not wait_for_ack(ser):
            print(RED + f"\nError: No ACK for chunk {i // CHUNK_SIZE}" + RESET)
            return False
        print(".", end="", flush=True)
    return True

def send_ota_sequence(ser, filepath):
    try:
        with open(filepath, 'rb') as f:
            fw_data = f.read()
    except FileNotFoundError:
        print(f"[Error] File not found: {filepath}")
        return

    fw_size = len(fw_data)
    fw_crc  = crc32(fw_data)

    print(f"Firmware size: {fw_size} bytes")
    print(f"CRC32: 0x{fw_crc:08X}")

    print("Sending OTA_START")
    send_cmd(ser, CMD_START)
    time.sleep(0.1)

    print("Sending header")
    send_header(ser, fw_size, fw_crc)
    time.sleep(0.1)

    print("Sending firmware data...")
    if not send_data_chunks(ser, fw_data):
        print(RED + "\nAborting OTA update due to NACK or timeout." + RESET)
        return

    print("Sending OTA_END")
    send_cmd(ser, CMD_END)

def read_from_uart(ser):
    while True:
        try:
            with ser_lock:
                line = ser.readline()
            if line:
                print("    " + GREEN + line.decode(errors='ignore').strip() + RESET)
        except:
            continue

def main():
    with serial.Serial(SERIAL_PORT, BAUDRATE, timeout=0.1) as ser:
        time.sleep(2)
        print("Connected. Type: ota, run, help, send\n")

        threading.Thread(target=read_from_uart, args=(ser,), daemon=True).start()

        while True:
            try:
                cmd = input().strip()
                if not cmd:
                    continue
                if cmd == "send":
                    filepath = input("Enter firmware file path: ").strip()
                    send_ota_sequence(ser, filepath)
                else:
                    ser.write((cmd + '\n').encode())
            except KeyboardInterrupt:
                print("\nExiting.")
                break

if __name__ == "__main__":
    main()

