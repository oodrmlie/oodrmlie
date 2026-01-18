import sysconfig
import sys
import serial
import datetime
import time
import importlib
import os

"""
Radar Data Logger - Serial interface for mmWave radar data acquisition.

This script connects to an ESP32 running the radar firmware via USB serial
and logs the received radar data to a CSV file. It handles both framed binary
packets and line-based text output from the ESP32, automatically detecting
the format and writing timestamped data to daily log files.

Features:
- Automatic daily CSV file creation with unique naming
- Dual mode: frame-based binary parsing and line-based text capture
- Robust serial port handling with buffer management
- Real-time console output with file logging

Usage:
    python radarLogger.py

Output Format:
    CSV with columns: timestamp, raw (space-separated radar values)

Written by: Kasper Schröder
"""

#Serial port configuration - adjust COM_PORT for your system
COM_PORT = "COM5" #Change to the COM port used by your device
Baud_RATE = 115200

#CSV file structure
HEADER = ["timestamp", "raw"]

#Frame protocol constants for binary packet detection
FRAME_HEADER = [0xAA, 0xBF, 0x10, 0x14]  #Marks start of radar frame
FRAME_TAIL   = [0xFD, 0xFC, 0xFB, 0xFA]  #Marks end of radar frame

#Create data directory if it doesn't exist
DATA_DIRECTORY = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIRECTORY, exist_ok=True)

def import_stdlib(name):
    """
    Import a module from Python's standard library, avoiding local conflicts.
    
    This ensures we get the stdlib csv module instead of any local csv.py file.
    
    Args:
        name: Name of the standard library module to import
        
    Returns:
        The imported module
    """
    stdlib_path = sysconfig.get_paths().get("stdlib")
    if not stdlib_path or not os.path.isdir(stdlib_path):
        raise ImportError("Cannot locate stdlib path")
    script_dir = os.path.abspath(os.path.dirname(__file__))
    removed = False
    try:
        if script_dir in sys.path:
            sys.path.remove(script_dir)
            removed = True
        module = importlib.import_module(name)
    finally:
        if removed:
            sys.path.insert(0, script_dir)
    return module

csv = import_stdlib("csv")

def today_filepath():
    """
    Generate a unique filename for today's radar data log.
    
    Creates filenames in format: YYYY-MM-DD.csv
    If the file exists, adds a suffix: YYYY-MM-DD-1.csv, YYYY-MM-DD-2.csv, etc.
    
    Returns:
        Full path to a non-existing CSV file for today's data
    """
    date_str = datetime.date.today().isoformat()
    candidate = os.path.join(DATA_DIRECTORY, f"{date_str}.csv")
    suffix = 1
    while os.path.exists(candidate):
        candidate = os.path.join(DATA_DIRECTORY, f"{date_str}-{suffix}.csv")
        suffix += 1
    return candidate

def ensure_header(path):
    """
    Write CSV header row if file doesn't exist or is empty.
    
    Args:
        path: Path to the CSV file
    """
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        with open(path, mode="w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(HEADER)

def now_ts():
    """
    Get current timestamp as formatted string.
    
    Returns:
        Timestamp string in format "YYYY-MM-DD HH:MM:SS"
    """
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def parse_csv():
    """
    Main data acquisition loop - connect to ESP32 and log radar data.
    
    This function:
    1. Opens serial connection to ESP32
    2. Creates/opens today's CSV log file
    3. Continuously reads and parses radar data in two modes:
       - Binary framed packets (detected by header/trailer bytes)
       - Line-based text output (CSV format from ESP32)
    4. Writes timestamped data to CSV and console
    5. Handles Ctrl+C gracefully to stop logging
    """
    #Configure serial port parameters
    ser = serial.Serial()
    ser.port = COM_PORT
    ser.baudrate = Baud_RATE
    ser.timeout = 2
    ser.rtscts = False  #Disable hardware flow control  #Disable hardware flow control
    ser.dsrdtr = False
    #Disable DTR and RTS lines to prevent ESP32 reset on connection
    try: ser.dtr = False
    except Exception: pass
    try: ser.rts = False
    except Exception: pass

    ser.open()
    time.sleep(0.5)  #Allow time for connection to stabilize
    #Clear any stale data from the serial input buffer
    try:
        ser.reset_input_buffer()
    except Exception:
        try:
            ser.flushInput()
        except Exception:
            while ser.in_waiting:
                ser.readline()

    #Prepare today's log file with CSV header
    path = today_filepath()
    ensure_header(path)

    print(f"Listening on {COM_PORT} @ {Baud_RATE}. Writing to {path}. Ctrl+C to stop.")

    #Frame accumulator for binary packet parsing
    collecting = False
    frame_bytes = []

    try:
        with open(path, mode="a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            while True:
                #MODE 1: Binary frame parsing - detect and extract framed packets
                if ser.in_waiting:
                    chunk = ser.read(ser.in_waiting)
                    #Convert bytes to list of integers for pattern matching
                    ints = list(chunk)
                    i = 0
                    while i < len(ints):
                        b = ints[i]

                        #Look for frame header sequence to start collecting
                        if not collecting:
                            #Align on 4-byte header pattern
                            if i + 3 < len(ints) and ints[i:i+4] == FRAME_HEADER:
                                collecting = True
                                frame_bytes = []
                                i += 4
                                continue

                        if collecting:
                            #Accumulate bytes until frame tail is detected
                            if i + 3 < len(ints) and ints[i:i+4] == FRAME_TAIL:
                                #Complete frame received - write to CSV as hex string
                                ts = now_ts()
                                payload_hex = " ".join(
                                    ["{:02X}".format(x) for x in FRAME_HEADER + frame_bytes + FRAME_TAIL]
                                )
                                w.writerow([ts, payload_hex])
                                f.flush()
                                print(f"{ts}, {payload_hex}")
                                collecting = False
                                frame_bytes = []
                                i += 4
                                continue
                            else:
                                frame_bytes.append(b)
                                i += 1
                                continue

                        #Not in a frame - skip this byte
                        i += 1

                #MODE 2: Line-based text parsing - handle ESP32's CSV output format
                line_bytes = ser.readline()
                if line_bytes:
                    line = line_bytes.decode("utf-8", errors="ignore").strip()
                    if not line:
                        continue

                    #Check if line is in ESP32's CSV format: "timestamp,value1 value2 ..."
                    if "," in line and line[:4].isdigit():
                        #Parse and normalize ESP32's timestamp,raw format
                        ts_raw = line.split(",", 1)
                        ts = ts_raw[0].strip()
                        raw = ts_raw[1].strip()
                        w.writerow([ts, raw])
                        f.flush()
                        print(f"{ts}, {raw}")
                    else:
                        #Record debug/status messages from ESP32 as-is
                        w.writerow(["", line])
                        f.flush()
                        print(line)

                ser.timeout = 2

    except KeyboardInterrupt:
        print("Stopped by user.")
    finally:
        try: ser.close()
        except Exception: pass

if __name__ == "__main__":
    parse_csv()