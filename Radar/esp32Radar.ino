/*
ESP32 mmWave Radar Interface for Occupancy Detection

This firmware reads range-Doppler data from an mmWave radar sensor via Serial2
and streams it to a host computer via Serial. The system captures 320 values
(20 Doppler bins × 16 range gates) per frame with synchronized timestamps.

Features:
- Real-time timestamp synchronization from host computer
- Pause/resume control via serial commands
- Two output modes: raw single-line or framed debug display
- Automatic frame parsing with header/trailer detection

Hardware:
- ESP32 development board
- mmWave radar sensor connected to Serial2 (RX2=GPIO16, TX2=GPIO17)

Serial Commands:
- SETTIME YYYY-MM-DD HH:MM:SS.mmm : Synchronize ESP32 clock with host
- s or stop                       : Pause data streaming
- r or resume                     : Resume data streaming
- mode raw                        : Switch to single-line output format
- mode framed                     : Switch to 2D matrix debug format


Written by: Kasper Schröder

Based on example code by Engr. Shahzada Fahad:
https://www.electroniclinic.com/esp32-hmmd-mmwave-sensor-real-tests-blynk-iot/
*/

#include <Arduino.h>
#include <vector>
#include "time.h"

//Serial2 pin configuration for mmWave sensor communication
#define RX2_PIN 16
#define TX2_PIN 17

//Global state variables
uint32_t rdmap[20][16]; //Stores parsed range-Doppler map: 20 doppler bins × 16 range gates
bool paused = false;    //Pause flag for data streaming control
bool timeSet = false;   //Indicates whether ESP32 clock has been synchronized with host

static unsigned long lastPrint = 0;

//Output mode selector: true=single-line CSV format, false=2D matrix debug format
bool singleLinePrint = true; //Change to switch between print types

/*
  Purpose: Read frames from Serial2 (mmWave sensor) and print data to
  Serial for debugging. The sketch also supports sending a SETTIME
  command from the host (via Serial) and a small helper to send a
  single hex payload to the sensor via Serial2.

  Notes: This code is based on example code provided by Engr. Shahzada Fahad, through
  the website: https://www.electroniclinic.com/esp32-hmmd-mmwave-sensor-real-tests-blynk-iot/
*/

//Time helpers

//Set the system time from manual components received over Serial.
//This is used when the host sends a `SETTIME` command.
void setManualTime(int year, int month, int day, int hour, int minute, int second, int millis = 0) {
  //Convert calendar time to Unix timestamp structure
  struct tm tm;
  tm.tm_year = year - 1900;  //tm_year is years since 1900
  tm.tm_mon  = month - 1;     //tm_mon is 0-11
  tm.tm_mday = day;
  tm.tm_hour = hour;
  tm.tm_min  = minute;
  tm.tm_sec  = second;

  //Convert to Unix epoch time and set system clock with microsecond precision
  time_t t = mktime(&tm);
  struct timeval now = { .tv_sec = t, .tv_usec = millis * 1000 };
  settimeofday(&now, NULL);
}

/*
getTimestamp - Generate formatted timestamp string for data logging.

Returns: String in format "YYYY-MM-DD HH:MM:SS.mmm" or "Time Error" if clock not set
*/
String getTimestamp() {
  struct tm timeinfo;
  struct timeval tv;
  if (!getLocalTime(&timeinfo)) {
    return "Time Error";
  }
  gettimeofday(&tv, nullptr);

  char ts[32];
  //Format: YYYY-MM-DD HH:MM:SS.mmm (ISO 8601 compatible for easy parsing)
  snprintf(ts, sizeof(ts), "%04d-%02d-%02d %02d:%02d:%02d.%03ld",
           timeinfo.tm_year + 1900,
           timeinfo.tm_mon + 1,
           timeinfo.tm_mday,
           timeinfo.tm_hour,
           timeinfo.tm_min,
           timeinfo.tm_sec,
           (long)(tv.tv_usec / 1000));
  return String(ts);
}

//=============================================================================
//SETUP AND INITIALIZATION
//=============================================================================

/*
setup - Initialize serial communications and configure radar sensor.

This function runs once at startup to:
1. Initialize Serial (USB) for host communication at 115200 baud
2. Initialize Serial2 (GPIO16/17) for radar sensor communication at 115200 baud
3. Send initial configuration hex payload to radar sensor
*/
void setup() {
  Serial.begin(115200);

  unsigned long startAttemptTime = millis();
  while (!Serial && millis() - startAttemptTime < 2000) { delay(100); }
  Serial.println("Serial Monitor Initialized.");

  Serial2.begin(115200, SERIAL_8N1, RX2_PIN, TX2_PIN);
  Serial.println("Serial2 Initialized on RX:" + String(RX2_PIN) + ", TX:" + String(TX2_PIN));

  //Send startup configuration payload to radar sensor
  //This hex string configures the radar operating mode (range resolution, frame rate, etc.)
  String hex_to_send = "FDFCFBFA0800120000000000000004030201"; //Change depending on wanted radar mode
  Serial.println("Sending Hex Data over Serial2...");
  sendHexData(hex_to_send);
  Serial.println("Hex Data Sent.");
}

//=============================================================================
//MAIN LOOP AND COMMAND PROCESSING
//=============================================================================

/*
loop - Main program loop for command processing and data streaming.

Continuously:
1. Checks for serial commands from host (SETTIME, pause/resume, mode switch)
2. Reads and parses radar data from Serial2 if not paused
3. Outputs formatted data to host via Serial
*/
void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    //Handle SETTIME command from host
    //Expected format: "SETTIME YYYY-MM-DD HH:MM:SS" or "SETTIME YYYY-MM-DD HH:MM:SS.mmm"
    if (cmd.startsWith("SETTIME")) {
      //Parse timestamp components from command string
      String payload = cmd.substring(8);
      payload.trim();

      int spaceIdx = payload.indexOf(' ');
      if (spaceIdx > 0) {
        String datePart = payload.substring(0, spaceIdx);
        String timePart = payload.substring(spaceIdx + 1);

        int year   = datePart.substring(0, 4).toInt();
        int month  = datePart.substring(5, 7).toInt();
        int day    = datePart.substring(8, 10).toInt();

        int dotIdx = timePart.indexOf('.');
        String secPart = (dotIdx >= 0) ? timePart.substring(6, dotIdx) : timePart.substring(6);
        String msPart  = (dotIdx >= 0) ? timePart.substring(dotIdx + 1) : String("0");

        int hour   = timePart.substring(0, 2).toInt();
        int minute = timePart.substring(3, 5).toInt();
        int second = secPart.toInt();
        int millis = msPart.toInt();

        setManualTime(year, month, day, hour, minute, second, millis);
        timeSet = true;
        Serial.println("Time updated from laptop!");
        Serial.print("Time updated to: ");
        Serial.println(getTimestamp());
      }
    }

    //Handle pause and resume commands
    if (cmd == "s" || cmd == "stop") {
      paused = true;
      Serial.println("Program paused. Send 'r' or 'resume' to continue.");
    } else if (cmd == "r" || cmd == "resume") {
      paused = false;
      Serial.println("Resuming program.");
    }

    //Mode selection: `mode raw` prints a single-line hex dump of the
    //Serial2 buffer; `mode framed` resumes framed packet parsing.
    if (cmd.equalsIgnoreCase("mode raw")) {
      singleLinePrint = true;
      Serial.println("Read mode: raw single-line hex dump");
    } else if (cmd.equalsIgnoreCase("mode framed") || cmd.equalsIgnoreCase("mode frame")) {
      singleLinePrint = false;
      Serial.println("Read mode: framed packet parsing");
    }
  }

  if (paused) {
    delay(50);
    return;
  }

  /*
  if (!timeSet) {
    // Skip parsing until RTC is valid
    delay(100);
    return;
  }
  */


  //Read from Serial2 using the selected reader method.
  readSerialData();
  //delay(1000);
}

//=============================================================================
//HEX DATA TRANSMISSION
//=============================================================================

/*
sendHexData - Convert hex string to bytes and send to radar sensor via Serial2.

This function takes a hex string (e.g., "AABBCCDD") and converts it to binary
bytes for transmission to the radar sensor. Used for sending configuration commands.

Parameter:
- hexString: String containing hex digits (must have even number of characters)
*/
void sendHexData(String hexString) {
  int hexStringLength = hexString.length();
  if (hexStringLength % 2 != 0) {
    Serial.println("Error: Hex string must have an even number of characters.");
    return;
  }
  int byteCount = hexStringLength / 2;
  byte hexBytes[byteCount];
  for (int i = 0; i < hexStringLength; i += 2) {
    String byteString = hexString.substring(i, i + 2);
    byte hexByte = (byte)strtoul(byteString.c_str(), NULL, 16);
    hexBytes[i / 2] = hexByte;
  }
  Serial.print("Sending "); Serial.print(byteCount); Serial.println(" bytes");
  Serial2.write(hexBytes, byteCount);
}

//=============================================================================
//RADAR DATA PARSING AND OUTPUT
//=============================================================================

/*
readSerialData - Read and parse radar frames from Serial2.

This function implements two output modes:
1. Single-line mode: Outputs CSV format "timestamp,val1 val2 ... val320"
2. Framed mode: Outputs 2D matrix (20×16) for debugging visualization

Radar frames are detected by header (0xAA...) and trailer (0xFDFCFBFA) bytes.
Each complete frame contains 320 uint32 values representing the range-Doppler map.
*/
void readSerialData() {
  if (singleLinePrint) {
    //Single-line CSV mode: output format "YYYY-MM-DD HH:MM:SS.mmm,val1 val2 ... val320"
    //This format is optimized for data logging and synchronization with camera timestamps
    static bool inFrame = false;
    static std::vector<uint8_t> frameBuf;

    while (Serial2.available() > 0) {
      byte b = Serial2.read();

      //Detect frame header (0xAA...) - marks start of new radar frame
      if (!inFrame && b == 0xAA) {
        frameBuf.clear();
        frameBuf.push_back(b);
        inFrame = true;
        continue;
      }

      if (inFrame) {
        frameBuf.push_back(b);
        //Detect frame trailer (FD FC FB FA) - marks end of radar frame
        int n = frameBuf.size();
        if (n >= 4 &&
            frameBuf[n - 4] == 0xFD &&
            frameBuf[n - 3] == 0xFC &&
            frameBuf[n - 2] == 0xFB &&
            frameBuf[n - 1] == 0xFA) {
          //Extract payload and verify frame contains exactly 320 values (20×16 RD map)
          int payloadLen = frameBuf.size() - 8;  //Exclude 4-byte header + 4-byte trailer
          int numValues = payloadLen / 4;         //Each value is 4 bytes (uint32)
          if (numValues == 320) {
          //Build CSV line: timestamp followed by space-separated values
          String line = getTimestamp();
          line += ",";
          for (int i = 0; i < numValues; i++) {
              //Convert 4 bytes to uint32 (little-endian)
              uint32_t val = (uint32_t)frameBuf[4 + i*4] |
                  ((uint32_t)frameBuf[4 + i*4 + 1] << 8) |
                  ((uint32_t)frameBuf[4 + i*4 + 2] << 16) |
                  ((uint32_t)frameBuf[4 + i*4 + 3] << 24);
              line += String(val);
              if (i < numValues - 1) line += " ";
          }
          Serial.println(line);
      } else {
            Serial.print("Unexpected frame length: ");
            Serial.println(numValues);
          }
          inFrame = false;
        }
      }
    }
  } else {
    //Framed debug mode: collect and parse complete frames, then display as 20×16 matrix
    //This mode is useful for visualizing the range-Doppler map during development
    static bool inFrame = false;
    static std::vector<uint8_t> frameBuf;

    while (Serial2.available() > 0) {
      byte b = Serial2.read();

      //Detect frame header (0xAA) - depends on radar mode configuration
      if (!inFrame && b == 0xAA) {
        frameBuf.clear();
        frameBuf.push_back(b);
        inFrame = true;
        continue;
      }

      if (inFrame) {
        frameBuf.push_back(b);

        //Detect frame trailer (FD FC FB FA) - depends on radar mode configuration
        int n = frameBuf.size();
        if (n >= 4 &&
            frameBuf[n - 4] == 0xFD &&
            frameBuf[n - 3] == 0xFC &&
            frameBuf[n - 2] == 0xFB &&
            frameBuf[n - 1] == 0xFA) {
          parseDebugFrame(frameBuf);
          inFrame = false;
        }
      }
      
    }
  }
}

/*
parseDebugFrame - Parse complete radar frame and display as 2D matrix.

Extracts 320 uint32 values from frame buffer, organizes them into the
20×16 range-Doppler map structure, and prints with timestamp for debugging.

Parameter:
- buf: Complete frame buffer including header and trailer
*/
void parseDebugFrame(const std::vector<uint8_t>& buf) {
  int payloadLen = buf.size() - 8;
  int numValues = payloadLen / 4; //should be 320
  if (numValues != 320) {
    Serial.print("Unexpected frame length: ");
    Serial.println(numValues);
    return;
  }

  //Convert frame bytes to uint32 values and organize into range-Doppler map
  //Data layout: 320 values arranged as 20 doppler bins (rows) × 16 range gates (columns)
  for (int i = 0; i < numValues; i++) {
    uint32_t val = (uint32_t)buf[4 + i*4] |
                   ((uint32_t)buf[4 + i*4 + 1] << 8) |
                   ((uint32_t)buf[4 + i*4 + 2] << 16) |
                   ((uint32_t)buf[4 + i*4 + 3] << 24);
    //Map linear index to 2D array: doppler (row) and range (column)
    int doppler = i / 16;      //Which doppler bin (0-19)
    int rangeGate = i % 16;    //Which range gate (0-15)
    rdmap[doppler][rangeGate] = val;
  }

  String ts = getTimestamp();
  if (ts == "Time Error") {
    ts = "Time not set yet";
  }
  Serial.print(ts + " ");
  Serial.println();

  //Print 20×16 matrix: each row is a doppler bin, each column is a range gate
  for (int i = 0; i < 20; i++) {
    for (int j = 0; j < 16; j++) {
      Serial.print(rdmap[i][j]);
      Serial.print(" ");
    }
    Serial.println();
  }
  //delay(10000);
}

/*
print_serial2_hex_line - Debug utility to dump raw Serial2 data as hex.

Prints all available bytes from Serial2 buffer as hexadecimal values.
Useful for debugging communication issues or analyzing raw sensor output.
*/
void print_serial2_hex_line() {
  if (Serial2.available() == 0) {
    Serial.println("No Serial2 data available to dump.");
    return;
  }

  String ts = getTimestamp();
  if (ts == "Time Error") ts = "Time not set yet";

  Serial.print(ts);
  Serial.print(", ");

  //Read and print all available bytes as padded hex
  while (Serial2.available() > 0) {
    byte b = Serial2.read();
    if (b < 16) Serial.print('0');
    Serial.print(b, HEX);
    Serial.print(' ');
  }
  Serial.println();
}

