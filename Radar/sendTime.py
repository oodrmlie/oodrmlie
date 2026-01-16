import serial
import datetime
import time

"""
Time Synchronization Utility for ESP32 Radar System.

This module sends the current computer time to the ESP32 via serial connection,
allowing the radar system to timestamp data frames accurately. The ESP32 firmware
receives the SETTIME command and updates its internal clock, ensuring radar data
and camera data can be synchronized based on their timestamps.

The synchronization is critical for:
- Multi-sensor data fusion (radar + camera)
- Accurate temporal analysis of occupancy patterns
- Matching radar frames with camera detections

Usage:
    python sendTime.py

Written by: Kasper Schröder
"""

#Serial port configuration - adjust COM_PORT for your system
COM_PORT = "COM5"  #Change to the COM port used by your device
BAUD_RATE = 115200

def send_time():
    """
    Send current computer datetime to ESP32 as SETTIME command.

    This function:
    1. Captures the current system time with millisecond precision
    2. Formats it as "SETTIME YYYY-MM-DD HH:MM:SS.mmm"
    3. Opens serial connection without triggering ESP32 reset
    4. Sends the command to ESP32
    5. Waits for and displays any acknowledgment from ESP32
    
    The ESP32 firmware parses this command and updates its internal RTC,
    ensuring all subsequent radar frames are tagged with accurate timestamps.
    """
    #Capture current time with microsecond precision
    current_dt = datetime.datetime.now()
    #Format: "SETTIME YYYY-MM-DD HH:MM:SS.mmm" (milliseconds, not microseconds)
    time_command = current_dt.strftime("SETTIME %Y-%m-%d %H:%M:%S.") + f"{current_dt.microsecond // 1000:03d}\n"

    #Open serial port with careful control line management to prevent ESP32 reset
    #Setting dsrdtr=False prevents pyserial from toggling DTR on connection
    serial_connection = serial.Serial(COM_PORT, BAUD_RATE, timeout=2, dsrdtr=False)
    
    #Disable RTS (Request To Send) line - prevents ESP32 from entering bootloader mode
    try:
        serial_connection.rts = False
    except Exception:
        pass
    
    #Disable DTR (Data Terminal Ready) line - prevents ESP32 reset on connection
    try:
        serial_connection.setDTR(False)
    except Exception:
        try:
            serial_connection.dtr = False
        except Exception:
            pass
    
    #Disable hardware flow control to ensure simple UART communication
    serial_connection.rtscts = False  #No RTS/CTS flow control
    serial_connection.dsrdtr = False  #No DSR/DTR flow control
    
    time.sleep(0.5)  #Allow serial connection to stabilize

    #Send SETTIME command to ESP32
    serial_connection.write(time_command.encode("utf-8"))
    print("Sent:", time_command.strip())

    #Wait for ESP32 to process command and send acknowledgment
    time.sleep(1)
    #Read and display any confirmation messages from ESP32
    while serial_connection.in_waiting:
        reply = serial_connection.readline().decode("utf-8", errors="ignore").strip()
        print("Device replied:", reply)

    serial_connection.close()  #Close connection to free the port


if __name__ == "__main__":
    send_time()