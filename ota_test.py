import serial
import threading

SERIAL_PORT = '/dev/ttyACM0'  # Update as needed
BAUDRATE = 115200

def read_from_uart(ser):
    while True:
        try:
            line = ser.readline()
            if line:
                print(line.decode(errors='ignore').strip())
        except:
            break

def main():
    with serial.Serial(SERIAL_PORT, BAUDRATE, timeout=0.1) as ser:
        print("Connected to STM32. Listening for output...\n")
        
        reader = threading.Thread(target=read_from_uart, args=(ser,), daemon=True)
        reader.start()

        while True:
            try:
                user_input = input()  # Wait for user input
                ser.write((user_input + '\n').encode())  # Send over UART
            except KeyboardInterrupt:
                print("\nExiting.")
                break

if __name__ == "__main__":
    main()

