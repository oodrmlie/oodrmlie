import time
import subprocess
import sys
import os
import shutil

"""
Radar System Automation Script - Upload firmware and start data logging.

This script automates the complete radar setup workflow:
1. Compiles and uploads the ESP32 radar firmware using arduino-cli
2. Sends time synchronization command to the ESP32
3. Starts the radar data logger to capture and save data

Requirements:
- arduino-cli must be installed and in PATH
- ESP32 board support must be installed in arduino-cli
- Correct BOARD_FQBN and PORT must be configured below

Usage:
    python run.py

Written by: Kasper Schröder
"""

#File paths for radar components
esp32SketchFile = "esp32Radar.ino"  #ESP32 firmware sketch directory  #ESP32 firmware sketch directory

loggerFile = "radarLogger.csv"  #Data logger script
sendTimeFile = "sendTime.py"     #Time synchronization script

#Arduino CLI configuration - adjust these for your setup
BOARD_FQBN = "esp32:esp32:esp32" #Fully-qualified board name for ESP32
UPLOAD_WAIT = 3  #Seconds to wait after upload for board to reboot  #Seconds to wait after upload for board to reboot

PORT = "COM5"  #Serial port for ESP32 connection (change as needed)


def run_cmd(cmd, check=True):
    """
    Execute a shell command and print it for visibility.
    
    Args:
        cmd: List of command and arguments to execute
        check: If True, raise exception on non-zero exit code
        
    Returns:
        CompletedProcess instance from subprocess.run
    """
    print("Running:", " ".join(cmd))
    return subprocess.run(cmd, check=check)


def upload_sketch_with_arduino_cli(esp32SketchFile) -> bool:
    """
    Compile and upload Arduino sketch to ESP32 using arduino-cli.
    
    This function:
    1. Checks if arduino-cli is installed and available in PATH
    2. Verifies that the sketch directory exists
    3. Compiles the sketch for the specified board (BOARD_FQBN)
    4. Uploads the compiled binary to the ESP32 via serial port (PORT)
    
    Args:
        esp32SketchFile: Path to the Arduino sketch directory (must contain .ino file)
        
    Returns:
        True if compilation and upload succeeded, False otherwise
        
    Note:
        Requires arduino-cli to be installed with ESP32 board support.
    """
    #Locate arduino-cli executable in system PATH
    cli = shutil.which("arduino-cli") or shutil.which("arduino-cli.exe")
    if not cli:
        return False

    #Verify sketch directory exists before attempting compilation
    if not os.path.isdir(esp32SketchFile):
        print(f"Sketch directory not found: {esp32SketchFile}")
        return False

    try:
        #Step 1: Compile the sketch for the target board
        run_cmd([cli, "compile", "--fqbn", BOARD_FQBN, esp32SketchFile])
        #Step 2: Upload compiled binary to ESP32 via serial port
        run_cmd([cli, "upload", "-p", PORT, "--fqbn", BOARD_FQBN, esp32SketchFile])
    except subprocess.CalledProcessError as e:
        print("Upload failed:", e)
        return False

    return True

if __name__ == "__main__":
    """
    Main execution workflow:
    1. Upload ESP32 firmware (if arduino-cli available)
    2. Wait for board reboot
    3. Send time synchronization to ESP32
    4. Start radar data logger
    """
    try:
        #Attempt to upload firmware to ESP32
        uploaded = upload_sketch_with_arduino_cli(esp32SketchFile)
        if uploaded:
            print("Upload succeeded, waiting for board to reboot")
            time.sleep(UPLOAD_WAIT)  #Allow ESP32 to restart and initialize

        #Synchronize ESP32 clock with computer time for accurate timestamps
        subprocess.run([sys.executable, sendTimeFile])
        time.sleep(UPLOAD_WAIT)  #Brief pause before starting logger
        
        #Start continuous radar data logging (runs until Ctrl+C)
        subprocess.run([sys.executable, loggerFile])
    except KeyboardInterrupt:
        print("Stopped by user.")  #shutdown on Ctrl+C