import serial
import threading

SERIAL_PORT = '/dev/ttyACM0'
BAUDRATE = 115200

def read_from_uart(ser):
    while True:
        try:
            line = ser.readline()
            if line:
                print(line.decode(errors='ignore').strip())
        except:
            break

def send_file(ser, filepath):
    try:
        with open(filepath, 'rb') as f:
            print(f"Sending file: {filepath}")
            while True:
                chunk = f.read(128)
                if not chunk:
                    break
                ser.write(chunk)
                time.sleep(0.01)  # brief delay between chunks
            ser.write(b'OTA_END\n')
            print("File send complete.")
    except FileNotFoundError:
        print(f"[Error] File not found: {filepath}")
    except PermissionError:
        print(f"[Error] Permission denied: {filepath}")
    except Exception as e:
        print(f"[Error] Failed to send file: {e}")


def main():
    with serial.Serial(SERIAL_PORT, BAUDRATE, timeout=0.1) as ser:
        print("Connected. Type commands: ota, run, help, send\n")
        threading.Thread(target=read_from_uart, args=(ser,), daemon=True).start()
        
        while True:
            try:
                cmd = input("> ").strip()
                if not cmd:
                    continue
                if cmd == "send":
                    filepath = input("Enter firmware file path: ").strip()
                    send_file(ser, filepath)
                else:
                    ser.write((cmd + '\n').encode())
            except KeyboardInterrupt:
                print("\nExiting.")
                break

if __name__ == "__main__":
    import time
    main()

